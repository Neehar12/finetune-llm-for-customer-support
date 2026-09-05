# Split report

- Rows after NA drop: 26872
- Exact duplicates removed (intent + normalised instruction + normalised response): 1
- Rows used: 26871
- Paraphrase groups: 5635 (threshold 0.6, similarity: tfidf)
- Largest group size: 138

## Split sizes
- train: 25173
- test: 1100
- val: 598

## Intent coverage in test (rows per intent)
- cancel_order: 37
- change_order: 46
- change_shipping_address: 36
- check_cancellation_fee: 36
- check_invoice: 44
- check_payment_methods: 45
- check_refund_policy: 37
- complaint: 50
- contact_customer_service: 37
- contact_human_agent: 45
- create_account: 38
- delete_account: 43
- delivery_options: 37
- delivery_period: 38
- edit_account: 41
- get_invoice: 37
- get_refund: 40
- newsletter_subscription: 37
- payment_issue: 54
- place_order: 38
- recover_password: 40
- registration_problems: 37
- review: 39
- set_up_shipping_address: 40
- switch_account: 47
- track_order: 40
- track_refund: 41

## Leakage: max TF-IDF cosine of each test instruction to any train instruction

| split strategy | mean max sim | >=0.8 | >=0.9 | exact |
|---|---|---|---|---|
| random_rows | 0.769 | 44.2% | 22.5% | 17.5% |
| group_aware | 0.611 | 10.0% | 1.1% | 0.0% |

Group-aware numbers will not be zero: paraphrases within an intent share vocabulary by construction. The point is the drop relative to the random baseline.
