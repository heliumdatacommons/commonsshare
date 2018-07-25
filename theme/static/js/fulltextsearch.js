function search() {
    $("#message").html("<span><i class='fa fa-refresh fa-spin'></i> querying documents... </span>");
    var term = $("#q").val();
    $.get('/ftsearch/?q=' + term , function(response){
      $("#message").html(response.message);
      $("#results").empty();
      $("#results").append("<th>ID</th><th>Filename</th><th>Description</th>");
      response.results.forEach(function(result){
        $("#results").append("<tr><td><a href='/uploads/" + result.filename + "'>" + result.id + "</td><td> " + result.filename + "</td><td>" + result.desc + " </td></tr>")
      })
    })
}

$(document).ready(function () {
    $("#search").click(search);
    $('#q').keypress(function (e) {
        if (e.which == 13 && ($("#q").val() !== undefined)) {
            search();
        }
    });
});
