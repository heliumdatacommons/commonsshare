function hd_search() {
    var term = $("#hd_q").val();
    $.get('/hdsearch/?q=' + term , function(response) {
      $("#hd_result").empty();
      if (response.results.length === 0)
          $('#hd_no_result').show();
      else {
          $('#hd_no_result').hide();
          response.results.forEach(function (result) {
              var defi_res = '';
              var curie_res = '';
              var curie_url_prefix = 'https://putmantime.github.io/HeliumPhenotypeSearch/';
              if (result.definitions)
                  defi_res = result.definitions;
              if (result.curie)
                  curie_res = '<a href="' + curie_url_prefix + result.curie + '">' + result.curie + '</a>';
              $("#hd_result").append(
                  "<tr><td>" + result.iri + "</td><td>" + result.labels + "</td><td>" +
                  curie_res + "</td><td>" + result.categories + "</td><td>" +
                  result.synonyms + "</td><td>" + defi_res + "</td></tr>");
          });
      }
    });
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
        content: '<p>Type a search term to search for all variations of the term. It uses SciGraph Ontology services in the Monarch initiative. Visit <a href="https://monarchinitiative.org/page/services" target="_blank">Monarch Initiative Services</a> for details.</p>',
        trigger: 'click'
    });
});
