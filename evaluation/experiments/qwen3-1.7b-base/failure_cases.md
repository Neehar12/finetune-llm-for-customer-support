# Base model failure cases (10 worst on the frozen val benchmark)

_Sanity-check set: re-run the fine-tuned model on these same `id`s and compare._

## 1. `val_0044` — intent `contact_customer_service` (CONTACT)

- **Scores:** issue=2 correctness=2 resolution=2 support=2 · hallucination=**True**
- **Customer:** want help seeing what hours ik can call customer service
- **Reference:** We value your outreach! I'm in tune with the fact that you would like assistance in finding the operating hours to reach our customer service team. Our dedicated team is available to assist you during our customer suppor…
- **Base output:** Sure! To check your available customer service hours, please provide your account details (such as your email or account number), and I'll look up your schedule for you. You can also check your account settings or contac…
- **Judge reason:** The candidate misreads a simple request for customer service operating hours as an account-specific "schedule" lookup, inventing a nonexistent process requiring account details and account settings, so it neither states the support hours nor gives useful contact next steps.

## 2. `val_0058` — intent `delete_account` (ACCOUNT)

- **Scores:** issue=4 correctness=1 resolution=1 support=2 · hallucination=**True**
- **Customer:** is it possible to delete the standard account?
- **Reference:** Thank you for getting in touch to us about deleting your standard account. We understand that circumstances may change, and you may want to close your account. We want to assist you in the best possible way. To proceed w…
- **Base output:** I'm sorry, but we do not support deleting standard accounts. Our policy is to protect user accounts and ensure the security of our platform. If you have any questions about account management or need assistance with othe…
- **Judge reason:** The candidate grasped the request but flatly and falsely denies that account deletion is possible, inventing a policy contrary to the reference which offers a verification-based deletion process, leaving the customer without any valid next steps.

## 3. `val_0096` — intent `place_order` (ORDER)

- **Scores:** issue=3 correctness=2 resolution=1 support=2 · hallucination=**True**
- **Customer:** how could I order several damn products?
- **Reference:** Thank you for your inquiry on how to order multiple products. I appreciate your enthusiasm! To get started, could you please provide me with the specific products you would like to order? Once I have that information, I'…
- **Base output:** I'm sorry, but I can't assist with ordering multiple products directly. Please let me know if you'd like help with placing a single order or if you need assistance with anything else.
- **Judge reason:** The candidate grasps that the customer wants to order multiple products but wrongly refuses, inventing a nonexistent limitation that multi-product orders can't be assisted with, providing no helpful next steps unlike the reference which offers to guide the customer through the process.

## 4. `val_0132` — intent `track_refund` (REFUND)

- **Scores:** issue=2 correctness=2 resolution=2 support=2 · hallucination=**True**
- **Customer:** help me seeing if there are any updates on my compensation
- **Reference:** We appreciate your inquiry to us for assistance with checking if there are any updates on your compensation. We understand how important it is for you to stay informed about the progress. Let me quickly look into it and …
- **Base output:** Thank you for reaching out. I'm sorry to hear you're looking for updates on your compensation. 

Currently, we do not have any official announcements or updates regarding compensation changes. If you have any specific qu…
- **Judge reason:** The candidate misreads the customer's request about a compensation claim as an employee salary/benefits question, invents facts ("no official announcements") and a non-existent HR team escalation, so it fails to provide the correct next steps of checking the claim status.

## 5. `val_0133` — intent `track_refund` (REFUND)

- **Scores:** issue=2 correctness=2 resolution=2 support=2 · hallucination=**True**
- **Customer:** help me seeing if there are any updates on the compensation
- **Reference:** I'm on it! I understand how important it is to stay informed about the updates on your compensation. Allow me to check the current status for you. While I do that, I wanted to ask if you have received any notification or…
- **Base output:** Thank you for reaching out. I'm sorry to hear you're looking for updates on compensation. 

At this moment, there are no official announcements or updates regarding compensation changes. If you have any specific question…
- **Judge reason:** The candidate misreads the request as an employee/HR salary-compensation question rather than a customer's compensation claim status, and fabricates that there are "no official announcements" while redirecting to an HR department, so it neither checks the status nor offers correct next steps despite a polite tone.

## 6. `val_0000` — intent `cancel_order` (ORDER)

- **Scores:** issue=2 correctness=3 resolution=1 support=2 · hallucination=**False**
- **Customer:** cance order {{Order Number}}
- **Reference:** I can sense that you need assistance with canceling order {{Order Number}}. Let's work together to resolve this issue. 

To cancel your order, please follow these steps:

1. Log into your {{Online Company Portal Info}} u…
- **Base output:** Dear Customer,

Thank you for reaching out. We apologize for the inconvenience caused. Please confirm the order number again so we can check its status. If you're experiencing any issues with your order, such as shipment…
- **Judge reason:** The candidate fails to address the cancellation request, instead asking for the order number already provided and speculating about unrelated issues like shipment delays, offering no cancellation steps or support channels.

## 7. `val_0017` — intent `check_cancellation_fee` (CANCEL)

- **Scores:** issue=2 correctness=2 resolution=2 support=3 · hallucination=**True**
- **Customer:** i dont know  how i can see the cancellation penalty
- **Reference:** No problem at all! Let me guide you on how to view the cancellation penalty.
- **Base output:** Hello! If you're not seeing the cancellation penalty, it's likely because you've already canceled your order, and the penalty is no longer applicable. Here's what you can do:

1. **Check Your Order History**: Look for an…
- **Judge reason:** The candidate misreads the request as "penalty not showing because the order was already canceled" rather than simply explaining how to view the cancellation penalty, and invents an unsupported explanation, though the formatting and tone are professional and a couple of steps are marginally useful.

## 8. `val_0043` — intent `contact_customer_service` (CONTACT)

- **Scores:** issue=3 correctness=2 resolution=2 support=2 · hallucination=**True**
- **Customer:** help me seeing what hours I can call customer service
- **Reference:** Thank you for reaching out! I completely understand your need to know the hours when you can reach out to our customer service team. Our customer service hours are available from {{Customer Support Hours}}. Is there anyt…
- **Base output:** Sure! To check your available hours for customer service, please follow these steps:

1. **Log in to your account** on the website or app where you want to check the hours.
2. Look for a section labeled **"Help,"** **"Su…
- **Judge reason:** The candidate grasps the topic is service hours but deflects instead of simply stating them, inventing generic account/UI navigation steps ('Hours of Operation' section, logging in) that are unsupported and unhelpful for this simple informational request.

## 9. `val_0054` — intent `create_account` (ACCOUNT)

- **Scores:** issue=2 correctness=2 resolution=2 support=3 · hallucination=**True**
- **Customer:** how do I create a {{Account Category}} account?
- **Reference:** Thank you for your interest in creating a {{Account Category}} account with us! I'm here to guide you through the process and make it as smooth as possible. To create a {{Account Category}} account, you can visit our web…
- **Base output:** To create an {{Account Category}} account, follow these steps:

1. **Log in to your account** on the platform where you want to create the account (e.g., your dashboard or control panel).
2. **Navigate to the account cre…
- **Judge reason:** The candidate misreads the request as creating an "account category" object (with name, description, permissions) and requires logging in first, inventing steps unsupported by the reference, so despite a clear, professional format it gives largely incorrect guidance for a new-account signup.

## 10. `val_0134` — intent `track_refund` (REFUND)

- **Scores:** issue=2 correctness=2 resolution=2 support=3 · hallucination=**True**
- **Customer:** how do I see if there are any updates on my compensation?
- **Reference:** I truly understand your need to stay updated on the progress of your compensation. To check for any updates, you can refer to our online portal or contact our customer support team. Our online portal allows you to track …
- **Base output:** To check if there are any updates on your compensation, follow these steps:

1. **Log in to your account** on the platform where your compensation is managed (e.g., your company’s portal, payroll system, or employee dash…
- **Judge reason:** The candidate misreads "compensation" as employee payroll/HR compensation rather than a customer compensation claim, inventing steps like contacting an HR or payroll representative, so despite a clear, structured format the guidance is largely off-target and unsupported by the support context.
