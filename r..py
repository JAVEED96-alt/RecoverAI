import razorpay

client = razorpay.Client(auth=("rzp_test_TSOCZmI4jf58eb", "XczaxX4dU0LjTBY3tkI0SqMq"))

# Fetch all payments
payments = client.payment.all()
print(payments)

# Fetch a single payment
payment = client.payment.fetch("pay_xxxxxxxxxxxx")
print(payment)