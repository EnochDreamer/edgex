const paymentForm = document.getElementById('paymentForm');
//const course=document.getElementById('course');
        paymentForm && paymentForm.addEventListener("submit", payWithPaystack, false);
        function payWithPaystack(e) {
            console.log(e)
            e.preventDefault();
            const courseId=e.target.dataset.courseId
            let handler = PaystackPop.setup({
                key: 'pk_live_fc12081cb873356e63159c45f996986266b99ad0', // Replace with your public key
                email: document.getElementById("email-address").value,
                amount: document.getElementById("amount").value * 100,
                // label: "Optional string that replaces customer email"
                onClose: function () {
                    alert('Window closed.');
                },
                callback: function (response) {
                   console.log(courseId)
                    fetch(`/courses/${courseId}/verify_pay/${response.reference}?amount=${document.getElementById("amount").value * 100}`)
                    .then((res)=>res.json())
                    .then((data)=>{
                        data.success?location.replace('/subscriptions'):alert('payment not successful')
                    })

                }
            });
            handler.openIframe();
        }
