/* javascript files for fews unblobbed: handling filter trees and parameters */

function applyTreeView() {
    $("#navigation").treeview({
        collapsed: true
    });
}

// (Re-)bind (possible) workspaceitems to the draggingmechanism.
// req: $("a.url-lizard-map-session-workspace-add-item-temp").attr("href");
function applyDragging() {
    // Parameters are draggable to workspaces.
    $(".workspace-acceptable").draggable({
        scroll: 'false',
        cursor: 'move',
        helper: 'clone',
        appendTo: 'body',
        revert: 'true',
        placeholder: 'ui-sortable-placeholder'
    });

    // Clicking a workspace-acceptable shows it in the 'temp' workspace.
    $(".workspace-acceptable").bind({
        click: function(event) {
            $(".workspace-acceptable").removeClass("selected");
            $(this).addClass("selected");
            var name = $(this).attr("name");
            var layer_method = $(this).attr("layer_method");
            var layer_method_json = $(this).attr("layer_method_json");
            var url_add_item_temp = $("a.url-lizard-map-session-workspace-add-item-temp").attr("href");
            $.post(url_add_item_temp,
                   { name: name,
                     layer_method: layer_method,
                     layer_method_json: layer_method_json
                   },
                   function(workspace_id){
                       updateLayer(workspace_id);
                   }
                  );
            stretchOneSidebarBox();
        }
    });
}

function applyClickingOnFilter() {
    // Clicking a filter highlights it and loads its parameters.
    $(".file").click(function(){
        var id = $(this).attr('id');
        var url_fews_parameter_tree_base = $("a.url-fews-parameter-tree-base").attr("href");
        $("#navigation li.selected").removeClass("selected");
        $(this).parent("li").addClass("selected");
        $("#parametertree").load(
            url_fews_parameter_tree_base + id + "/37551/",
            function() {
                applyDragging();
            });
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

