# Benchmark report — `qwen3-1.7b-base`

- **Model:** `qwen3:1.7b` (served via Ollama)
- **Judge:** `claude-opus-5`
- **Benchmark:** evaluation/data/benchmark/val_benchmark.jsonl (135 items, validation split, frozen)
- **Thinking:** False  ·  **Generation:** `{"temperature": 0.0, "top_p": 1.0, "seed": 42, "num_predict": 512}`
- **System prompt:** You are a customer support assistant for an online business. A customer has sent you a message. Respond directly to the customer in a helpful, professional, and empathetic tone. Understand what they need, give accurate information, and clearly explain any steps required to resolve their request. Keep the response focused and concise.

## Overall

| metric | n | understanding | correctness | resolution | support | halluc. rate |
|---|---|---|---|---|---|---|
| **overall** | 135 | 4.319 | 3.585 | 3.215 | 3.474 | 0.437 |

## By category (sorted by resolution quality)

| category | n | understanding | correctness | resolution | support | halluc. rate |
|---|---|---|---|---|---|---|
| CONTACT | 10 | 2.9 | 2.7 | 2.2 | 2.7 | 0.5 |
| ORDER | 20 | 4.6 | 3.25 | 2.95 | 3.35 | 0.5 |
| DELIVERY | 10 | 4.4 | 3.7 | 3.0 | 3.4 | 0.4 |
| REFUND | 15 | 3.933 | 3.2 | 3.067 | 3.333 | 0.5333 |
| INVOICE | 10 | 4.0 | 3.4 | 3.1 | 3.4 | 0.4 |
| ACCOUNT | 30 | 4.367 | 3.667 | 3.133 | 3.567 | 0.4333 |
| PAYMENT | 10 | 4.5 | 4.1 | 3.4 | 3.4 | 0.1 |
| CANCEL | 5 | 4.4 | 3.8 | 3.6 | 3.8 | 0.4 |
| SUBSCRIPTION | 5 | 4.8 | 4.0 | 3.8 | 3.8 | 0.8 |
| FEEDBACK | 10 | 4.9 | 3.9 | 3.9 | 3.7 | 0.5 |
| SHIPPING | 10 | 4.8 | 4.4 | 4.2 | 4.1 | 0.3 |

## By intent (sorted by resolution quality)

| intent | n | understanding | correctness | resolution | support | halluc. rate |
|---|---|---|---|---|---|---|
| cancel_order | 5 | 4.4 | 2.6 | 2.0 | 2.8 | 0.6 |
| contact_customer_service | 5 | 3.0 | 2.2 | 2.0 | 2.0 | 0.8 |
| check_payment_methods | 5 | 4.0 | 3.2 | 2.2 | 2.4 | 0.2 |
| track_refund | 5 | 3.0 | 2.2 | 2.2 | 2.8 | 1.0 |
| contact_human_agent | 5 | 2.8 | 3.2 | 2.4 | 3.4 | 0.2 |
| switch_account | 5 | 4.4 | 4.4 | 2.6 | 3.4 | 0.4 |
| create_account | 5 | 3.6 | 2.6 | 2.8 | 3.2 | 0.6 |
| delete_account | 5 | 4.6 | 3.0 | 2.8 | 3.0 | 0.8 |
| delivery_options | 5 | 4.4 | 3.8 | 2.8 | 3.4 | 0.4 |
| recover_password | 5 | 4.2 | 2.8 | 2.8 | 3.0 | 0.6 |
| track_order | 5 | 4.4 | 3.2 | 2.8 | 3.2 | 0.4 |
| get_invoice | 5 | 4.4 | 3.2 | 3.0 | 3.2 | 0.6 |
| check_invoice | 5 | 3.6 | 3.6 | 3.2 | 3.6 | 0.2 |
| delivery_period | 5 | 4.4 | 3.6 | 3.2 | 3.4 | 0.4 |
| change_order | 5 | 5.0 | 3.4 | 3.4 | 3.6 | 0.4 |
| get_refund | 5 | 4.2 | 3.4 | 3.4 | 3.4 | 0.4 |
| check_cancellation_fee | 5 | 4.4 | 3.8 | 3.6 | 3.8 | 0.4 |
| check_refund_policy | 5 | 4.6 | 4.0 | 3.6 | 3.8 | 0.2 |
| edit_account | 5 | 4.6 | 4.4 | 3.6 | 4.2 | 0.0 |
| place_order | 5 | 4.6 | 3.8 | 3.6 | 3.8 | 0.6 |
| newsletter_subscription | 5 | 4.8 | 4.0 | 3.8 | 3.8 | 0.8 |
| review | 5 | 5.0 | 3.8 | 3.8 | 3.6 | 0.4 |
| complaint | 5 | 4.8 | 4.0 | 4.0 | 3.8 | 0.6 |
| change_shipping_address | 5 | 4.8 | 4.4 | 4.2 | 4.0 | 0.2 |
| registration_problems | 5 | 4.8 | 4.8 | 4.2 | 4.6 | 0.2 |
| set_up_shipping_address | 5 | 4.8 | 4.4 | 4.2 | 4.2 | 0.4 |
| payment_issue | 5 | 5.0 | 5.0 | 4.6 | 4.4 | 0.0 |

## Example cases

### Strongest

**intent:** `set_up_shipping_address`  ·  **category:** `SHIPPING`

- **Customer:** I don't know how to set up my shipping address
- **Reference:** I've got that you're unsure about how to set up your shipping address. Let's work together to get it done:

1. Log in to your account on our website.
2. Navigate to the "My Account" or "Profile" section.
3. Look for the option labeled "Shipping Addresses" or something similar.
4. Click on it to access the shipping address settings.
5. Select the option to "Add New Address" or "Edit Shipping Address".
6. Fill in the required fields with the accurate information for your shipping address.
7. Double-check the details to ensure accuracy.
8. Save or update the changes you made.

If you encounter any issues or you need further assistance during this process, please don't hesitate to let me know. I'm here to help you every step of the way.
- **Base output:** Sure! Let's walk through how to set up your shipping address step by step:

1. **Log in to your account**: Go to the website and click on your username or profile icon to access your account.

2. **Navigate to the shipping section**: Look for a section labeled "Shipping," "Address," or "Account Settings."

3. **Edit your address**: Click on "Edit" or "Update" next to your current shipping address.

4. **Enter your details**: Fill in your full name, street address, city, state, and ZIP code. You may also need to enter a phone number if required.

5. **Save your changes**: Click "Save" or "Update" to confirm your new address.

If you're still having trouble, feel free to let me know, and I can guide you through the specific steps for your account.
- **Judge:** issue=5 · correctness=5 · resolution=5 · support=5 · hallucination=**False**
- **Reason:** The candidate accurately understands the request and provides clear, correct, generic step-by-step instructions closely matching the reference, with a friendly offer of further help and no invented specifics.

**intent:** `set_up_shipping_address`  ·  **category:** `SHIPPING`

- **Customer:** I don't know how to enter the new delivery address
- **Reference:** I've understood that entering a new delivery address can be confusing, but don't worry, I'm here to help you through the process. To enter a new delivery address, follow these steps:

1. Log in to your account.
2. Navigate to the "Shipping" or "Delivery" section.
3. Look for an option to "Add New Address" or "Edit Address."
4. Click on that option.
5. Fill in the required fields with the details of your new delivery address, such as street, city, state, and zip code.
6. Double-check the entered information for accuracy.
7. Save the changes.

If you encounter any difficulties while following these steps or if the process appears different on your device or platform, please provide me with additional details so that I can assist you further. Your satisfaction is my top priority.
- **Base output:** Hello! I'm sorry you're having trouble entering the new delivery address. Here's how you can do it:

1. **Log in to your account**.
2. **Go to the 'Delivery Addresses' section**.
3. **Click on 'Add New Address'**.
4. **Fill in the details**:
   - **First Name**
   - **Last Name**
   - **Street Address**
   - **City**
   - **State**
   - **ZIP Code**
   - **Country**
5. **Click 'Save' to add the address**.

If you need further assistance, feel free to ask!
- **Judge:** issue=5 · correctness=5 · resolution=5 · support=5 · hallucination=**False**
- **Reason:** The candidate correctly interprets the request and provides clear, accurate, generic step-by-step instructions closely matching the reference, with a professional tone and no invented policies (specific form fields are ordinary, reasonable detail).

### Weakest

**intent:** `cancel_order`  ·  **category:** `ORDER`

- **Customer:** cance order {{Order Number}}
- **Reference:** I can sense that you need assistance with canceling order {{Order Number}}. Let's work together to resolve this issue. 

To cancel your order, please follow these steps:

1. Log into your {{Online Company Portal Info}} using your credentials.
2. Navigate to the '{{Online Order Interaction}}' or '{{Online Order Interaction}}' section to access your order details.
3. Look for the specific order with the number {{Order Number}} and click on it.
4. Within the order details, you should find a '{{Online Order Interaction}}' option. Please select it to initiate the cancellation process.
5. The system may prompt you with additional questions to confirm your cancellation. Please provide the necessary information when asked.
6. Once the cancellation process is completed, you will receive a confirmation notification.

If you encounter any difficulties or have further questions, our dedicated customer support team is available to assist you. You can reach them during {{Customer Support Hours}} at {{Customer Support Phone Number}} or through the Live Chat feature on our {{Website URL}}. Your satisfaction is our top priority, and we appreciate your patience throughout this process.
- **Base output:** Dear Customer,

Thank you for reaching out. We apologize for the inconvenience caused. Please confirm the order number again so we can check its status. If you're experiencing any issues with your order, such as shipment delays or payment problems, please let us know and we'll do our best to assist you.

Best regards,  
[Your Name]  
Customer Support Team
- **Judge:** issue=2 · correctness=3 · resolution=1 · support=2 · hallucination=**False**
- **Reason:** The candidate fails to address the cancellation request, instead asking for the order number already provided and speculating about unrelated issues like shipment delays, offering no cancellation steps or support channels.

**intent:** `contact_customer_service`  ·  **category:** `CONTACT`

- **Customer:** want help seeing what hours ik can call customer service
- **Reference:** We value your outreach! I'm in tune with the fact that you would like assistance in finding the operating hours to reach our customer service team. Our dedicated team is available to assist you during our customer support hours. To get in touch, you can call our customer service hotline at {{Customer Support Phone Number}} or connect with us through the Live Chat feature on our website at {{Website URL}}. Feel free to reach out if you have any further questions or concerns. We're here to help!
- **Base output:** Sure! To check your available customer service hours, please provide your account details (such as your email or account number), and I'll look up your schedule for you. You can also check your account settings or contact customer service directly via phone to confirm your hours. Let me know how you'd like to proceed!
- **Judge:** issue=2 · correctness=2 · resolution=2 · support=2 · hallucination=**True**
- **Reason:** The candidate misreads a simple request for customer service operating hours as an account-specific "schedule" lookup, inventing a nonexistent process requiring account details and account settings, so it neither states the support hours nor gives useful contact next steps.


---
_Raw artifacts in this folder: `generations.jsonl`, `evaluation_results.jsonl` (per-example scores + reasons), `aggregate_metrics.json`, `generation_config.json`._
