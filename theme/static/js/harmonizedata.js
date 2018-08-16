function hd_search() {
    var term = $("#hd_q").val();
    $.get('/hdsearch/?q=' + term , function(response) {
      $("#hd_result").empty();
      if (response.results.length === 0)
          $('#hd_no_result').show();
      else {
          $('#hd_no_result').hide();
          response.results.forEach(function (result) {
              $("#hd_result").append(
                  "<tr><td>" + result.iri + "</td><td>" + result.labels + "</td><td>" +
                  result.curie + "</td><td>" + result.categories + "</td><td>" +
                  result.synonyms + "</td><td>" + result.definitions + "</td></tr>");
          });
      }
    })
}

$(document).ready(function () {
    $("#hd_search").click(hd_search);
    $('#hd_q').keypress(function (e) {
        if (e.which == 13 && ($("#hd_q").val() !== undefined)) {
            hd_search();
        }
    });
    $("#hd-help-info").popover({
        html: true,
        container: '#body',
        content: '<p>Type a search term to search for all variations of the term.</p>',
        trigger: 'click'
    });
});
