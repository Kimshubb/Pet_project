//add hovered class to selected list item and remove it from others
//let list = document.querySelectorAll('.navigation li');

//function activeLink() {
    //list.forEach((item) =>
      //  item.classList.remove('hovered'));
    //this.classList.add('hovered');
//}
//list.forEach((item) => item.addEventListener('mouseover', activeLink));

//dashboard toggle
//let toggle = document.querySelector('.toggle');
//let navigation = document.querySelector('.navigation');
//let main = document.querySelector('.main');

//toggle.onclick = function () {
  //  navigation.classList.toggle('active');
    //main.classList.toggle('active');
//}

// Path: register student modal
// Initialization for ES Users

//import { Modal, Ripple, initMDB } from "mdb-ui-kit";

//initMDB({ Modal, Ripple });

// new payment student suggestions
$(document).ready(function(){
    $("#student_name").on("input", function(){
        var query = $(this).val();
        if(query.length > 2){
            $.ajax({
                url: "/student_suggestions",
                data: { query: query },
                success: function(data){
                    var suggestions = $("#suggestions");
                    suggestions.empty();
                    suggestions.show();
                    data.forEach(function(student){
                        suggestions.append('<div class="suggestion-item list-group-item" data-id="' + student.id + '">' + student.name + '</div>');
                    });
                },
                error: function(xhr, status, error) {
                    console.log("AJAX error: ", error);
                }
            });
        } else {
            $("#suggestions").hide();
        }
    });

    $(document).on("click", ".suggestion-item", function(){
        var studentId = $(this).data("id");
        var studentName = $(this).text();
        console.log("Selected student ID:", studentId);  // Debug log
        $("#student_name").val(studentName);
        $("#student_id").val(studentId);
        $("#suggestions").hide();
    });

    $(document).click(function(event) {
        if (!$(event.target).closest("#suggestions, #student_name").length) {
            $("#suggestions").hide();
        }
    });
});

// print fee statement fuct in fee_statement.html
<script>
    function printDiv(divName) {
        var printContents = document.getElementById(divName).innerHTML;
        var originalContents = document.body.innerHTML;
        document.body.innerHTML = printContents;
        window.print();
        document.body.innerHTML = originalContents;
        location.reload();  // Reload the page to restore the original content
    }
</script>