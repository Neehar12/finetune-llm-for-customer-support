# Judge prompt comparison — v1 vs v2 (base model, n=135, same generations)

Both runs score the identical `qwen3-1.7b-base` generations with Claude Opus 5; only the judge prompt differs.

## Overall means

| dimension | v1 | v2 | Δ |
|---|---|---|---|
| issue_understanding | 4.319 | 3.941 | -0.378 |
| correctness | 3.585 | 3.467 | -0.118 |
| resolution_quality | 3.215 | 3.007 | -0.208 |
| support_quality | 3.474 | 3.770 | +0.296 |
| hallucination_rate | 0.437 | 0.452 | +0.015 |

## Agreement
| dimension | exact% | within ±1 | mean\|Δ\| |
|---|---|---|---|
| issue_understanding | 60.7% | 100.0% | 0.393 |
| correctness | 77.8% | 100.0% | 0.222 |
| resolution_quality | 74.8% | 100.0% | 0.252 |
| support_quality | 62.2% | 99.3% | 0.385 |

Hallucination: agree 127/135 (94%); v1 flagged 59, v2 flagged 61.

## Largest disagreements

### `val_0134` — track_refund (Δtotal +4)
- Customer: how do I see if there are any updates on my compensation?
- v1: issue_understanding=2, correctness=2, resolution_quality=2, support_quality=3, halluc=True — The candidate misreads "compensation" as employee payroll/HR compensation rather than a customer compensation claim, inventing steps like contacting an HR or payroll representative, so despite a clear, structured format the guidance is largely off-target and unsupported by the support context.
- v2: issue_understanding=3, correctness=3, resolution_quality=3, support_quality=4, halluc=True — The candidate correctly suggests checking the online account/compensation section, but wrongly frames the request as employee payroll/HR compensation and directs the customer to an 'HR or payroll representative' rather than the company's own customer support, an unsupported and misleading redirection.

### `val_0001` — cancel_order (Δtotal -3)
- Customer: cancel order
- v1: issue_understanding=5, correctness=4, resolution_quality=3, support_quality=4, halluc=False — The candidate correctly identifies the cancellation intent and gives clear, professional generic steps, but it deflects to "contact customer support" rather than directly asking for the order number and handling the cancellation itself, making it less actionable than the reference.
- v2: issue_understanding=4, correctness=3, resolution_quality=2, support_quality=4, halluc=True — The candidate recognizes the cancellation intent but deflects the customer to 'contact customer support' (when it is the support channel) and asserts unsupported channels (phone, email, live chat) rather than simply asking for the order number to proceed, leaving the issue largely unresolved despite clear, professional writing.

### `val_0005` — change_order (Δtotal -3)
- Customer: I cannot update purchase {{Order Number}}
- v1: issue_understanding=5, correctness=4, resolution_quality=4, support_quality=4, halluc=False — The candidate correctly grasps that the customer can't update an order and offers reasonable generic troubleshooting plus a request for details, though telling the customer to "contact customer support" while acting as support is slightly incoherent and some steps are assumed rather than grounded, and it never asks what change the customer wants to make.
- v2: issue_understanding=4, correctness=3, resolution_quality=3, support_quality=4, halluc=True — The candidate acknowledges the issue and asks for clarifying details, but it invents unsupported troubleshooting specifics (account 'restricted' status, order states like 'Processing'/'Pending' blocking updates) without knowing what update the customer is attempting, making the guidance speculative rather than the reference's appropriate clarification-first approach.

### `val_0014` — change_shipping_address (Δtotal -3)
- Customer: have a question about an address update
- v1: issue_understanding=4, correctness=4, resolution_quality=4, support_quality=4, halluc=False — The candidate correctly identifies the address-update topic and offers clear, professional next steps, though it assumes the customer wants an immediate change rather than first inviting their actual question, and asking for the reason for the update is somewhat unnecessary.
- v2: issue_understanding=3, correctness=3, resolution_quality=3, support_quality=4, halluc=True — The customer only signaled they have a question about an address update, but the candidate assumes they want to perform the change, requests unnecessary personal details (including a reason for the change), and implies it can directly execute the update 	hough the being clear and polite in tone.

### `val_0037` — complaint (Δtotal -3)
- Customer: I am very unhappy with your service, I try to lodge a claim
- v1: issue_understanding=5, correctness=4, resolution_quality=4, support_quality=4, halluc=True — The candidate correctly grasps the customer's desire to lodge a complaint and offers reasonable next steps with an empathetic tone, but it invents unverified channels (a 'customer support portal', phone/email options) not supported by the reference, and its apology/empathy is somewhat thinner than the reference.
- v2: issue_understanding=4, correctness=3, resolution_quality=3, support_quality=4, halluc=True — The candidate acknowledges the complaint and offers to help, but it asserts unsupported specific channels (a customer support portal, phone/email) instead of directly guiding the claim process, and pushing options back to the customer is less effective than simply gathering details to resolve the issue.

### `val_0065` — delivery_period (Δtotal -3)
- Customer: I am trying to find shipping periods, could you help me?
- v1: issue_understanding=4, correctness=4, resolution_quality=3, support_quality=3, halluc=True — The candidate grasps the customer's general need and appropriately asks for clarification, but it breaks the support persona by referencing external platforms like Amazon or Shopify (unsupported context) instead of simply requesting the order/tracking number, and its verbose, checklist-style formatting is less appropriate for a customer-facing reply.
- v2: issue_understanding=3, correctness=3, resolution_quality=2, support_quality=3, halluc=False — The candidate asks clarifying questions but frames itself as a generic third-party assistant asking which platform (Amazon, Shopify) the customer uses, which is off-context for a company's own support agent; it fails to request the order/tracking number needed to actually look up shipping timelines, leaving the customer with little actionable progress.

### `val_0084` — get_refund (Δtotal -3)
- Customer: i need help to get refunds of my money
- v1: issue_understanding=5, correctness=4, resolution_quality=4, support_quality=4, halluc=False — The candidate correctly grasps the refund request and asks reasonable clarifying questions like the reference, though asking for account credentials and referencing an external 'seller or platform' is slightly off-context for a first-party support agent and it doesn't outline the refund process itself.
- v2: issue_understanding=4, correctness=4, resolution_quality=3, support_quality=3, halluc=False — The candidate appropriately asks for clarifying details as the reference does, but the question 'Which product or service were you purchasing from?' and 'Have you already contacted the seller or platform?' frame the company as a third party rather than the merchant, and asking for account information like name/email in chat is questionable; it also offers no concrete next steps toward the refund.

### `val_0098` — place_order (Δtotal -3)
- Customer: where can i order an article
- v1: issue_understanding=5, correctness=3, resolution_quality=4, support_quality=4, halluc=True — The candidate correctly grasps the customer's intent and offers a clear, professional next step with an invitation for more detail, but it invents unverified specifics (a "Shop" section and an unfilled website URL) rather than clarifying which article is wanted as the reference does.
- v2: issue_understanding=4, correctness=3, resolution_quality=3, support_quality=3, halluc=True — The candidate understands the intent and offers actionable steps, but invents an unsupported website "Shop" section and leaves a raw "[insert website URL]" placeholder visible to the customer, making the guidance unverified and unpolished.
