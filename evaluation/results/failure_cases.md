# Failure cases — where the tuned model still struggles

(test split, Q4_K_M/Ollama, Opus-5 v2 judge)

## CANCEL — the one category where hallucination did NOT improve (33% -> 33%)

### `test-0125` — check_cancellation_fee (CANCEL)

**Customer:** where can i see the termniation penalty

**BASE** {'issue_understanding': 4, 'correctness': 2, 'resolution_quality': 2, 'support_quality': 4, 'hallucination': True}

> You can find the termination penalty in your contract with us. Typically, it is outlined in the terms and conditions section of your agreement. If you'd like, I can help you locate it more specifically by checking the relevant section of your contract.

**TUNED** {'issue_understanding': 5, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> To view the termination penalty, you can access your account online and navigate to the "Terms and Conditions" section. There, you will find detailed information about the termination penalty and any associated fees.

**Judge (tuned):** The candidate correctly grasps the intent and is well-written, but directs the customer to a "Terms and Conditions" section rather than the correct "Termination Charges" section, an unsupported specific instruction that could send the customer to the wrong place.

**Reference:** To find information about the termination penalty, you can log in to your account and navigate to the "Termination Charges" section. There, you will be able to see the details and amount of the penalty.

---

### `test-0129` — check_cancellation_fee (CANCEL)

**Customer:** i dont know what to do to see the termination penalty

**BASE** {'issue_understanding': 1, 'correctness': 2, 'resolution_quality': 1, 'support_quality': 3, 'hallucination': True}

> Thank you for reaching out. If you're not sure how to view the termination penalty, here's what you can do:

1. **Check Your Employment Agreement**: Look for a section that outlines termination penalties, usually in the employee handbook or contract.

2. **Review Your Notice of Termination**: If you've received a termination notice, check the details for any penalties or compensation.

3. **Contact Your Employer**: If you're still employed, speak with your HR or supervisor to clarify the terms.

4. **Consult a Legal Professional**: If you're unsure, consider consulting a labor lawyer to unders

**TUNED** {'issue_understanding': 5, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> No problem! To view the termination penalty, you can follow these steps:

1. Log in to your account on our website.
2. Navigate to the "Account Settings" or "Billing" section.
3. Look for the "Termination Fees" or "Cancellation Charges" option.
4. Click on it to view the details of the termination penalty.

If you encounter any difficulties or have further questions, feel free to reach out to our customer support team for assistance.

**Judge (tuned):** The candidate clearly understands the request and gives a well-organized, actionable path, but it invents specific account navigation steps ('Account Settings'/'Billing' > 'Termination Fees') not supported by context, whereas the reference points to FAQ/Terms and Conditions or customer service; the fabricated menu paths could mislead the customer.

**Reference:** No worries! Let me guide you through the process of checking the termination penalty. Firstly, you can visit our website and navigate to the "FAQ" or "Terms and Conditions" section. Here you should be able to find detailed information about the termination penalty. Alternatively, you can contact our customer service team who will be more than happy to assist you with any queries regarding the term

---

### `test-0132` — check_cancellation_fee (CANCEL)

**Customer:** i dont know how i can check the termination penalties

**BASE** {'issue_understanding': 1, 'correctness': 2, 'resolution_quality': 1, 'support_quality': 3, 'hallucination': True}

> Sure! To check your termination penalties, you should:

1. **Review Your Employment Agreement**: Look for any clauses related to termination, including notice periods, resignation payments, or penalties for termination.

2. **Check Your Company's Policies**: Many companies have internal policies about termination penalties. You can usually find these in your employee handbook or through your HR department.

3. **Consult Your Employer**: If you're unsure, contact your HR representative or employer directly. They can provide you with the specific terms applicable to your situation.

**TUNED** {'issue_understanding': 5, 'correctness': 2, 'resolution_quality': 2, 'support_quality': 4, 'hallucination': True}

> No problem! To check the termination penalties, you can follow these steps:

1. Log in to your account on our website.
2. Navigate to the "Account" or "Billing" section.
3. Look for the "Termination Fees" or "Cancellation Charges" tab.
4. Click on it to view the details of the termination penalties.

If you have any further questions or need assistance, feel free to reach out to our customer support team.

**Judge (tuned):** The candidate invents specific navigation steps and UI tabs ("Termination Fees"/"Cancellation Charges") that are unsupported by the context, whereas the reference directs the customer to their contract or customer service; the fabricated procedure could mislead the customer despite clear, professional presentation.

**Reference:** No worries! I can help you with that. To check the termination penalties, you can either refer to your contract or get in touch with our customer service team. They will be able to provide you with the specific details regarding the termination fees associated with your account.

---

### `test-0139` — check_cancellation_fee (CANCEL)

**Customer:** i dont know how to see the early termination penalty

**BASE** {'issue_understanding': 2, 'correctness': 2, 'resolution_quality': 2, 'support_quality': 3, 'hallucination': True}

> Sure! To see the early termination penalty, you typically need to check your contract or agreement. Here’s how you can do it:

1. **Review Your Contract**: Look for any section that mentions early termination penalties or clauses related to termination.
2. **Check for a "Notice Period"**: Some contracts require you to give a notice period before termination, and the penalty may be based on that.
3. **Contact Your Employer**: If you're an employee, check with your employer’s HR department or employee handbook.
4. **Consult a Legal Professional**: If you're unsure, consider consulting a legal ex

**TUNED** {'issue_understanding': 5, 'correctness': 2, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> No problem! To view the early termination penalty, you can follow these steps:

1. Log in to your account on our website.
2. Navigate to the "Account Settings" or "Billing" section.
3. Look for the "Cancellation Policy" or "Termination Fees" tab.
4. Click on it to view the details of the early termination penalty.

If you have any further questions or need assistance, feel free to reach out to our customer support team.

**Judge (tuned):** The candidate invents specific website navigation steps and tab names ("Cancellation Policy"/"Termination Fees") that are unsupported by the context, whereas the reference directs the customer to their agreement terms or support; the answer is well-organized and understands the intent, but the fabricated procedure risks misleading the customer.

**Reference:** No problem at all! To view the early termination penalty, you can check the terms and conditions of your agreement or contact our customer service team for assistance. They will be able to provide you with the necessary information.

---

## Other residual failures

### `test-0049` — change_order (ORDER)

**Customer:** I have to update order {{Order Number}}, how to do it?

**BASE** {'issue_understanding': 5, 'correctness': 2, 'resolution_quality': 2, 'support_quality': 4, 'hallucination': True}

> Sure! To update your order {{Order Number}}, please follow these steps:

1. Log in to your account.
2. Navigate to the "My Orders" section.
3. Find your order {{Order Number}} and click on it.
4. Click on "Edit" or "Update" to make the necessary changes.
5. Save your changes and confirm.

If you need further assistance, feel free to ask!

**TUNED** {'issue_understanding': 5, 'correctness': 2, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> We understand that you need to update order number {{Order Number}}. To assist you with this, please follow these steps:

1. Log in to your account on our website.
2. Navigate to the "Order History" section.
3. Locate the specific order with the number {{Order Number}}.
4. Click on the order to view the details.
5. Look for the "Update Order" option and select it.
6. Follow the prompts to make the necessary changes to your order.
7. Review the updated order details to ensure everything is correct.
8. If you encounter any issues or need further assistance, please don't hesitate to reach out to 

**Judge (tuned):** The candidate invents a specific self-service flow ("Order History" section, "Update Order" button) that is unsupported by the reference, which instead directs the customer to contact support; the answer is well-organized and clear but risks misleading the customer with fabricated UI steps.

**Reference:** We're here for you to us regarding your need to update order number {{Order Number}}. We appreciate your proactive approach in ensuring your order is accurate and up to date. To assist you with this, I recommend contacting our customer support team directly. They will provide you with the necessary instructions and guidance on how to update your order. Our dedicated team is available {{Customer Su

---

### `test-0054` — change_order (ORDER)

**Customer:** I have to edit order {{Order Number}}, how to do it?

**BASE** {'issue_understanding': 4, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> Certainly! To edit an order, follow these steps:

1. **Log in to your account**.
2. **Navigate to the orders section** (usually found under "My Orders" or "Orders").
3. **Find the order** you wish to edit and click on it.
4. **Click on "Edit"** next to the order.
5. **Make the necessary changes** (e.g., update shipping address, change payment method, adjust delivery date, etc.).
6. **Save your changes**.

If you need further assistance, feel free to ask!

**TUNED** {'issue_understanding': 5, 'correctness': 4, 'resolution_quality': 4, 'support_quality': 4, 'hallucination': True}

> We understand that you need to make changes to order number {{Order Number}}. We're here to assist you with that. To edit your order, you can follow these steps:

1. Log in to your account on our website or mobile app.
2. Go to the "Order History" or "My Orders" section.
3. Locate the specific order you want to edit (order number {{Order Number}}).
4. Click on the order to view the details.
5. Look for the "Edit" or "Modify" option and select it.
6. Make the desired changes to the order, such as adding or removing items, updating quantities, or modifying shipping details.
7. Review the changes

**Judge (tuned):** The candidate correctly identifies the intent and gives clear, actionable self-service steps with escalation options, but it asserts specific UI elements ("Edit"/"Modify" button, Order History section) and editing capabilities not supported by the context, which the reference instead handles by asking for details first.

**Reference:** I'm conscious of the reality that you need help editing order number {{Order Number}}. Making changes to an existing order is possible, and I'll be glad to guide you through the process. To get started, could you please provide me with more specific details about the changes you would like to make? This information will assist us in ensuring accurate and satisfactory modifications to your order.

---

### `test-0090` — change_shipping_address (SHIPPING)

**Customer:** wanna know more about correcting the address

**BASE** {'issue_understanding': 4, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> Certainly! If you'd like to correct your address, please provide the following details:

1. **Your current address** (street, city, state, ZIP code)
2. **The correct address** you'd like to use
3. **Reason for the correction** (e.g., typo, outdated, new address, etc.)

Once you provide this information, I’ll assist you in updating your address. Let me know how you'd like to proceed!

**TUNED** {'issue_understanding': 5, 'correctness': 3, 'resolution_quality': 4, 'support_quality': 4, 'hallucination': True}

> I'm happy to help! If you need to correct your address, you can easily do so by logging into your account and navigating to the "Address" section. From there, you can update your shipping address with the correct information. If you encounter any issues or need further assistance, feel free to reach out to our customer support team. They are available {{Customer Support Hours}} at {{Customer Support Phone Number}} or through the Live Chat on our website at {{Website URL}}. We're here to help make sure your shipping address is accurate and up to date.

**Judge (tuned):** The candidate correctly grasps the intent and offers clear, well-organized next steps, but asserts a specific self-service flow (an "Address" section in the account) that is unsupported by the context, whereas the reference directs the customer to contact support for the update.

**Reference:** Definitely! We're here to provide you with more information on correcting your address. If you need to make changes to your delivery address, please reach out to our customer support team and provide them with the correct address details. They will assist you in updating your address information and ensuring smooth delivery of your order.

---

### `test-0096` — change_shipping_address (SHIPPING)

**Customer:** there is an error modifying the delivery address

**BASE** {'issue_understanding': 3, 'correctness': 2, 'resolution_quality': 2, 'support_quality': 3, 'hallucination': True}

> Thank you for bringing this to our attention. We apologize for the inconvenience caused. 

To resolve this issue, please follow these steps:

1. **Check Your Internet Connection**: Ensure you have a stable internet connection.
2. **Clear Browser Cache**: Sometimes, browser cache issues can cause errors.
3. **Try a Different Browser or Device**: Test the functionality on another device or browser.
4. **Contact Support**: If the issue persists, please reach out to our support team at support@yourbusiness.com or call us at 123-456-7890. We will do our best to assist you.

We appreciate your patience

**TUNED** {'issue_understanding': 3, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> I apologize for the inconvenience caused by the error in modifying your delivery address. Our team is here to assist you in resolving this issue promptly. Please provide us with the correct address, and we will make sure to update it for you.

**Judge (tuned):** The candidate recognizes the address-change problem but skips gathering details about the actual error, instead asserting the team can manually update the address and guaranteeing it will be done, which is an unsupported claim about capability/outcome.

**Reference:** I'm sorry to hear that you're experiencing an error while trying to modify your delivery address. Could you please provide me with more details about the error so that I can assist you further?

---

### `test-0098` — change_shipping_address (SHIPPING)

**Customer:** I have an error modifying the address

**BASE** {'issue_understanding': 4, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> Thank you for reaching out. It seems you're having trouble modifying your address. Here are some steps you can try to resolve the issue:

1. **Check Permissions**: Ensure you have the necessary permissions to modify your address. If you're logged in as a guest, some features may be restricted.

2. **Clear Cache**: Sometimes, browser or app cache can cause issues. Try clearing your cache and restarting the application.

3. **Contact Support**: If the problem persists, please contact our customer support team. You can reach us via email at support@yourbusiness.com or through our live chat.

We'r

**TUNED** {'issue_understanding': 3, 'correctness': 3, 'resolution_quality': 2, 'support_quality': 4, 'hallucination': True}

> I apologize for the inconvenience caused by the error in modifying your address. To resolve this issue, please follow these steps: 
1. Log in to your account on our website.
2. Go to the "Account Settings" or "Profile" section.
3. Look for the option to edit your address.
4. Click on the edit button and make the necessary changes.
5. Save the updated address.
If you continue to experience difficulties, please reach out to our customer support team for further assistance.

**Judge (tuned):** The candidate ignores that the customer already encountered an error and instead gives generic navigation steps with invented UI specifics ('Account Settings'/'Profile'), failing to gather the error details needed to actually troubleshoot, and oddly refers the customer to support while acting as support.

**Reference:** I'm sorry to hear that you're experiencing difficulties when trying to modify your address. Can you please provide more details about the error you're encountering? This will help me assist you better and find a solution for you.

---

### `test-0103` — change_shipping_address (SHIPPING)

**Customer:** I don't know how I can correct my address

**BASE** {'issue_understanding': 3, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> I'm sorry you're having trouble with your address. Here's how you can correct it:

1. **Check for typos** in your address (street name, city, state, ZIP code).
2. **Log in to your account** (if you have one) and look for an "Address" or "Profile" section.
3. **Update your address** in the account settings.
4. **Verify** that the new address is correct by checking a few sources (e.g., USPS, local government).

If you need further assistance, feel free to let me know!

**TUNED** {'issue_understanding': 4, 'correctness': 3, 'resolution_quality': 3, 'support_quality': 4, 'hallucination': True}

> No worries! I can guide you through the process of correcting your address. First, log in to your account and navigate to the "Account Settings" section. From there, you should be able to find an option to update your shipping address. Make sure to enter the correct information and save the changes. If you encounter any difficulties, feel free to reach out to our customer support team for further assistance.

**Judge (tuned):** The candidate correctly identifies the address-correction intent and is clearly written, but it invents specific self-service UI steps ('Account Settings' section, shipping address option) that are unsupported and may not apply, instead of the reference's approach of collecting order details and updating the address on the customer's behalf.

**Reference:** Don't worry, we can assist you with correcting your address. Please provide us with your order details and the updated address, and we will make the necessary changes for you.

---

