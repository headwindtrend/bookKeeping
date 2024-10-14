# bookKeeping
This is a simple bookkeeping plugin which enables money transactions to be entered in relatively free format, as part of your diary records, yet the balance brought down and the arithmetic calculation are completed automatically. Besides, if you change a transaction in the past, all the subsequent transactions will also be updated automatically (iterating the bal b/d and arith recalc up to the most recent one.)

the plugin can handle normal chronological order (top down), as well as the bottom up style. if you want it in bottom up style, just add this `[=Bottom Up Style=]` somewhere in your file, say, at the very end (like one of my sample).

if you use it together with my `usefulsearch` plugin which provides a powerful shortlisting feature, you can easily review the transactions by account. for instance, enter this search pattern `[Cash=` to review all lines with cash transactions.

note: since the auto-recalc is triggered by the "=" character, if you delete a transaction in the past, you need to manually use the "=" for the one prior to the deleted one to trigger the recalc.

i included two sample files for you to try the features.

If you appreciate my work, i will be very grateful if you can support my work by making small sum donation thru PayPal with `Send payment to` entered as `headwindtrend@gmail.com`. Thank you very much for your support.
