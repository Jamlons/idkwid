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
        var inputText2 = $('#username').val();

        // Call the SQLi detection function
        if (SQLiDetection(inputText)) {
            event.preventDefault(); // Block form submission if SQLi characters are detected
        } else {
            console.log("Form submitted successfully, no SQLi detected.");
            // No preventDefault here, so the form will submit normally if no SQLi detected
        }
        if (SQLiDetection(inputText2)) {
            event.preventDefault(); // Block form submission if SQLi characters are detected
        } else {
            console.log("Form submitted successfully, no SQLi detected.");
            // No preventDefault here, so the form will submit normally if no SQLi detected
        }
    });
});

$(document).ready(function() {
    $('#file_input').on('submit', function(event) {
        event.preventDefault(); // Prevent the form from reloading the page

        // Create a FormData object from the form
        let formData = new FormData(this);

        // Send the form data via AJAX
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false, // Prevent jQuery from automatically transforming the data into a query string
            contentType: false, // Set the content type to false for multipart/form-data
            success: function(data) {
                $('#upload_status').removeClass('temp'); // Temp class is used to hide elements - make class visible.
                $('#upload_status').text(data.success);
            },
            error: function(jqXHR) {
                const error = jqXHR.responseJSON ? jqXHR.responseJSON.error : 'An error occurred';
                $('#upload_status').removeClass('temp'); // Temp class is used to hide elements - make class visible.
                $('#upload_status').text(error);
            }
        });
    });
});
