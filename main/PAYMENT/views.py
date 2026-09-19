from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
import json
from .models import Payment
from .khalti_service import KhaltiPaymentService
from question.models import Question, QuestionAssignment
from advisor.models import AdvisorProfile


@login_required
def initiate_payment(request, question_id):
    """
    Initiate payment for a question consultation
    """
    if request.user.role != "questioner":
        return HttpResponseBadRequest("Only questioners can make payments")
    
    question = get_object_or_404(
        Question,
        id=question_id,
        questioner=request.user
    )
    
    # Check if advisor is assigned
    assignment = QuestionAssignment.objects.filter(
        question=question,
        status='accepted'
    ).first()
    
    if not assignment:
        messages.error(request, "No advisor has been assigned to this question yet.")
        return redirect('question_detail', question_id=question.id)
    
    # Check if payment already exists
    existing_payment = Payment.objects.filter(
        question=question,
        status='completed'
    ).first()
    
    if existing_payment:
        messages.info(request, "Payment has already been completed for this question.")
        return redirect('question_detail', question_id=question.id)
    
    # Get advisor's consultation rate
    advisor = assignment.advisor
    amount = advisor.consultation_rate
    
    if amount <= 0:
        messages.error(request, "Advisor has not set a consultation rate yet. Please contact support.")
        return redirect('question_detail', question_id=question.id)
    
    print(f"Payment initiation: Amount={amount}, Advisor={advisor.user.username}, Question={question.id}")
    
    # Create pending payment record
    payment = Payment.objects.create(
        question=question,
        advisor=advisor,
        questioner=request.user,
        amount=amount,
        status='pending'
    )
    
    # Check payment mode
    payment_mode = getattr(settings, 'PAYMENT_MODE', 'test')
    
    if payment_mode == 'test':
        # Test mode: Auto-complete payment for development
        payment.mark_completed()
        messages.success(request, "Payment completed successfully! (Test Mode) You can now chat with the advisor.")
        return redirect('question_detail', question_id=question.id)
    
    # Sandbox or Production mode: Use Khalti payment gateway
    service = KhaltiPaymentService()
    
    print(f"Payment Mode: {payment_mode}")
    print(f"Using Khalti Base URL: {service.base_url}")
    
    callback_url = request.build_absolute_uri(
        reverse('payment_callback', args=[payment.id])
    )
    
    product_identity = f"question_{question.id}"
    product_name = f"Consultation for: {question.title}"
    
    return_url = request.build_absolute_uri(
        reverse('payment_return', args=[payment.id])
    )
    
    khalti_response = service.initiate_payment(
        amount=amount,
        product_identity=product_identity,
        product_name=product_name,
        callback_url=callback_url,
        return_url=return_url,
        website_url=request.build_absolute_uri('/'),
        product_url=request.build_absolute_uri(
            reverse('question_detail', args=[question.id])
        )
    )
    
    # Debug: Log the response for troubleshooting
    print(f"Khalti Response: {khalti_response}")
    
    # Check if Khalti payment initiation was successful
    if khalti_response.get('success', False) and khalti_response.get('payment_url'):
        # Redirect to Khalti payment page
        payment_url = khalti_response.get('payment_url')
        print(f"Redirecting to Khalti payment URL: {payment_url}")
        return redirect(payment_url)
    else:
        # Handle error
        payment.mark_failed()
        error_message = khalti_response.get('message', khalti_response.get('error', 'Unknown error'))
        messages.error(request, f"Failed to initiate payment: {error_message}. Please try again or contact support.")
        return redirect('question_detail', question_id=question.id)


@csrf_exempt
@require_POST
def payment_callback(request, payment_id):
    """
    Handle Khalti payment callback (webhook)
    """
    payment = get_object_or_404(Payment, id=payment_id)
    
    try:
        data = json.loads(request.body)
        pidx = data.get('pidx')
        
        if not pidx:
            return JsonResponse({'success': False, 'message': 'Missing required parameter: pidx'}, status=400)
        
        # Verify payment with Khalti
        service = KhaltiPaymentService()
        verification = service.verify_payment(pidx, payment.amount)
        
        if verification.get('success', False):
            # Mark payment as completed
            payment.mark_completed(
                txn_id=verification.get('transaction_id'),
                idx=pidx
            )
            return JsonResponse({'success': True, 'message': 'Payment verified successfully'})
        else:
            payment.mark_failed()
            return JsonResponse({'success': False, 'message': 'Payment verification failed'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        payment.mark_failed()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def payment_return(request, payment_id):
    """
    Handle return from Khalti payment page
    """
    # Try to get the payment without authentication first
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        # If payment doesn't exist, redirect to home
        return redirect('home')
    
    # Check if payment is still pending and verify it immediately
    if payment.status == 'pending':
        # Check if Khalti returned with success parameters
        pidx = request.GET.get('pidx') or request.GET.get('idx')
        status = request.GET.get('status')
        transaction_id = request.GET.get('transaction_id') or request.GET.get('txnId')
        
        if pidx and status == 'Completed':
            # Mark payment as completed immediately based on Khalti response
            payment.mark_completed(
                txn_id=transaction_id or 'khalti_completed',
                idx=pidx
            )
        elif status == 'User canceled':
            payment.mark_failed()
    
    # Redirect to login if user is not authenticated, otherwise to question detail
    if request.user.is_authenticated:
        if payment.status == 'completed':
            messages.success(request, "Payment completed successfully! You can now chat with the advisor.")
        elif payment.status == 'failed':
            messages.error(request, "Payment failed. Please try again.")
        else:
            messages.warning(request, f"Payment status: {payment.status}. Please wait.")
        return redirect('question_detail', question_id=payment.question.id)
    else:
        # User not authenticated, redirect to login with the payment return URL
        # The payment status has already been updated above
        return redirect(f'/login/?next=/payment/return/{payment_id}/')


@login_required
def payment_history(request):
    """
    View payment history for the current user
    """
    if request.user.role == "questioner":
        payments = Payment.objects.filter(
            questioner=request.user
        ).select_related('question', 'advisor', 'advisor__user').order_by('-created_at')
    elif request.user.role == "advisor":
        advisor = get_object_or_404(AdvisorProfile, user=request.user)
        payments = Payment.objects.filter(
            advisor=advisor
        ).select_related('question', 'questioner').order_by('-created_at')
    else:
        payments = Payment.objects.none()
    
    return render(request, 'payment/payment_history.html', {'payments': payments})


@login_required
def payment_detail(request, payment_id):
    """
    View details of a specific payment
    """
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Access control
    if request.user.role == "questioner":
        if payment.questioner != request.user:
            return HttpResponseBadRequest("Access Denied")
    elif request.user.role == "advisor":
        if payment.advisor.user != request.user:
            return HttpResponseBadRequest("Access Denied")
    else:
        return HttpResponseBadRequest("Access Denied")
    
    return render(request, 'payment/payment_detail.html', {'payment': payment})
