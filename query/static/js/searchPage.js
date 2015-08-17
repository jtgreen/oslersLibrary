$(document).ready(function(){    

            $('#searchButton').click(function(){
                $('#searchForm').submit()
            });
            
            /// NEEDED FOR CSRF TOKEN, AJAX - Relies on Jquery cookie plugin per (https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax)
            var csrftoken = $.cookie('csrftoken');
            
            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }
            $.ajaxSetup({
                crossDomain: false, // obviates need for sameOrigin test
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type)) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
            /// End setting CSRF Token ///
            
            $('.jqPagination').jqPagination({
                paged: function(page) {
                    
                    // Because this is dynamically generated in the search page, e.g.,
                    // depending on how this app was deployed, it could have a different root,
                    // for example: oslersLibrary/query/page... so, read it from the search box's
                    // action 
                    var posting = $.post( $("#searchForm").attr("action") + "page/" + page + "/" );
                    // Put the results in a div
                    posting.done(function( data ) {
                        $( "#queryResults" ).empty().append( data );
                    });
                }
            });
});