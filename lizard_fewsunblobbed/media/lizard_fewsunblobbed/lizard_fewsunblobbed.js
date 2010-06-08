/* javascript files for fews unblobbed: handling filter trees and parameters */

// The treeview js has been moved to lizard-ui

// The applydragging javascript has been moved to lizard-map.


function applyClickingOnFilter() {
    // TODO: replace by generic lizard-map reload functionality.
    // Clicking a filter highlights it and loads its parameters.
    $(".file").click(function(){
        var id = $(this).attr('id');
        var url_fews_parameter_tree_base = $("a.url-fews-parameter-tree-base").attr("href");
        $("#navigation li.selected").removeClass("selected");
        $(this).parent("li").addClass("selected");
        $("#parametertree").load(
            url_fews_parameter_tree_base + id + "/37551/");
        filterParameterAccordeon.click(1);
    });
}

// load the tree. !if the page is loaded, run this function!
// uses a.url-fews-filter-tree
function loadFilterTree() {
    var url_fews_filter_tree = $("a.url-fews-filter-tree").attr("href");
    if (url_fews_filter_tree !== undefined) {
        $.ajax({
            url: url_fews_filter_tree,
            context: document.body,
            success: function(data){
                $("#navigation").replaceWith(data);
                applyTreeView();
                applyClickingOnFilter();
                stretchOneSidebarBox();
            }
        });
    }
}

// Set up filter tree if page is loaded
$(document).ready(loadFilterTree);
