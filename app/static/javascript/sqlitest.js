$(document).ready(function() {
    // Define the SQLi detection function
    function SQLiDetection(inputText) {
        // SQL injection patterns (simple detection)
        var sqlKeywords = /(\b(SELECT|INSERT|DELETE|UPDATE|DROP|OR|AND|UNION|FROM|WHERE)\b)|['";\-\-#]/i;

        if (sqlKeywords.test(inputText)) {
            alert("Na ahhh no SQL injection allowed in this house.");
            return true; // Return true if SQLi characters are detected
        }
        return false; // Return false if no SQLi characters are detected
    }

    $('#index_input').on('submit', function(event) {
        var inputText = $('#password').val();

        // Call the SQLi detection function
        if (SQLiDetection(inputText)) {
            event.preventDefault(); // Block form submission if SQLi characters are detected
        } else {
            console.log("Form submitted successfully, no SQLi detected.");
            // No preventDefault here, so the form will submit normally if no SQLi detected
        }
    });
});
