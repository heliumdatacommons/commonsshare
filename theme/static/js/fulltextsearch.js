function search() {
    var term = $("#q").val();
    $.get('/ftsearch/?q=' + term , function(response) {
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
    $("#fts-help-info").popover({
        html: true,
        container: '#body',
        content: '<p>Type a query term to search for all variations of the term. Apache Lucene query syntax is supported. For example, you can add case sensitive boolean operators, e.g., AND, OR, NOT, in your search term query. Visit <a href="https://lucene.apache.org/core/2_9_4/queryparsersyntax.html" target="_blank">Apache Lucene Query Parser Syntax</a> for details.</p>',
        trigger: 'click'
    });
});
