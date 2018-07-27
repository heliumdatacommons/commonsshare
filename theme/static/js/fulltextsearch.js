function search() {
    $("#message").html("<span><i class='fa fa-refresh fa-spin'></i> querying documents... </span>");
    var term = $("#q").val();
    $.get('/ftsearch/?q=' + term , function(response) {
      $("#message").html(response.message);
      $("#results").empty();
      $("#results").append("<th>ID</th><th>Filename</th><th>Description</th>");
      $("#fts_result").empty();
      if (response.results.length === 0)
          $('#no_result').show();
      else {
          $('#no_result').hide();
          response.results.forEach(function (result) {
              $("#fts_result").append(
                  "<tr><td><strong><a href='" + result.file_url + "'>" +
                  result.filename + "</a></strong></td><td><strong><a href='" + result.res_url +
                  "' target=\"_blank\"'>" + result.res_title + "</a></strong></td><td>" +
                  result.res_creator + "</td><td>" + result.res_create_time + "</td><td>" +
                  result.res_update_time + "</td><td>" + result.score + "</td></tr>");
          });
      }
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
