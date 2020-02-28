var translations = {
    "Filtrar...": {
        'en-US': "Filter..."
    }
};

function updateTranslation(){
    $('.translateHtml').each(function(){
        if (translations[$(this).html()]) {
            if (userLang == "ptt-BR") {
                if (translations[$(this).html()]["pt-BR"]) {
                    $(this).html(translations[$(this).html()]["pt-BR"]);
                }
            } else {
                if (translations[$(this).html()]["en-US"]) {
                    $(this).html(translations[$(this).html()]["en-US"]);
                }
            };
        };
    });
    $('.translateVal').each(function(){
        if (translations[$(this).attr("value")]) {
            if (userLang == "ptt-BR") {
                if (translations[$(this).attr("value")]["pt-BR"]) {
                    $(this).attr("value", translations[$(this).attr("value")]["pt-BR"]);
                }
            } else {
                if (translations[$(this).attr("value")]["en-US"]) {
                    $(this).attr("value", translations[$(this).attr("value")]["en-US"]);
                }
            };
        };
    });
    $('.translateTitle').each(function(){
        if (translations[$(this).attr("title")]) {
            if (userLang == "ptt-BR") {
                if (translations[$(this).attr("title")]["pt-BR"]) {
                    $(this).attr("title", translations[$(this).attr("title")]["pt-BR"]);
                }
            } else {
                if (translations[$(this).attr("title")]["en-US"]) {
                    $(this).attr("title", translations[$(this).attr("title")]["en-US"]);
                }
            };
        };
    });
    $('.translatePlaceholder').each(function(){
        if (translations[$(this).attr("placeholder")]) {
            if (userLang == "ptt-BR") {
                if (translations[$(this).attr("placeholder")]["pt-BR"]) {
                    $(this).attr("placeholder", translations[$(this).attr("placeholder")]["pt-BR"]);
                }
            } else {
                if (translations[$(this).attr("placeholder")]["en-US"]) {
                    $(this).attr("placeholder", translations[$(this).attr("placeholder")]["en-US"]);
                }
            };
        };
    });
};

String.prototype.rsplit = function(sep, maxsplit) {
    var split = this.split(sep);
    return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
}

function scrollToAnchor(aid){
    var aTag = $(aid);
    $('html,body').animate({scrollTop: aTag.offset().top},'slow');
};

function apagarCorpus(corpus){
    if (window.confirm('Tem certeza de que deseja apagar o corpus "' + corpus + '"?')) {
        window.location = '/cancelTrain?c=' + corpus + '&delete=True&callback=upload&golden=' + $(".deleteGoldenToo").is(":checked");
    };
};

function apagarCorpusGolden(corpus){
    if (window.confirm('Tem certeza de que deseja apagar o corpus golden "' + corpus + '"?')) {
        window.location = '/api/deleteGolden?c=' + corpus;
    };
};

if ($('.repoName').length) {
    $('.repoName').on('change', function(){
        loadingScreen();
        $button = $('#repoName');
        $.ajax({
            url: "/api/getCommits",
            method: "POST",
            data: {
                repoName: $button.val(),
            },
            success: function(data){
                $('.branchDiv').html(data['html']);
                $('.branch').selectpicker('refresh');
                atualizar();
                $('#branch').unbind('change').on('change', function(){
                    loadingScreen();
                    $buttonBranch = $('#branch');
                    $buttonRepo = $('#repoName');
                    $.ajax({
                        url: "/api/getCommits",
                        method: "POST",
                        data: {
                            repoName: $buttonRepo.val(),
                            branch: $buttonBranch.val(),
                        },
                        success: function(data){
                            $('.repoCommitDiv').html(data['html']);
                            $('.repoCommit').selectpicker('refresh');
                            $('.branch').selectpicker('refresh');
                            atualizar();
                        }
                    });
                });
            },
        })
    });
};

function atualizar(){

    updateTranslation();

    $('.matrixTd').children("a").click(function(){
        $(".matrixTd").css("background-color", "white");
        $(this).parents(".matrixTd").css("background-color", "yellow");
    });

    $('.drag').draggable({
        zIndex: 100,
        revert: true,
        opacity: 0.35,
        appendTo: "body",
        refreshPositions: true,
        
    });
      
    $('tr').droppable({
        hoverClass: "drop-hover",
        drop: function(event, ui) {
            var classes = ui.draggable.attr('class');
            if ($(this).children('.id').html().replace(/<input.*?">/g, '') != ui.draggable.siblings(".id").html().replace(/<input.*?">/g, '')){
                if (! ui.draggable.html().includes("<input")) {
                    ui.draggable.html(ui.draggable.html() + $comInput);
                };
                ui.draggable.html(ui.draggable.html().match(/<input.*?">/g)[0] + $(this).children('.id').html().replace(/<input.*?">/g, ''));
                ui.draggable.children('input').val(ui.draggable.html().replace(/<input.*?">/g, ''));
            };
        }
    });

    $('.notPipe').click(function(){
        document.execCommand('selectAll');
    });

    $('.valor').keydown(function(event){
        if((event.keyCode == 8 || event.keyCode == 46 || ((event.ctrlKey || event.metaKey) && event.keyCode == 65))) {
            if ( $(this).html().match(/<input.*?">/g)[0] ) {
                $comInput = $(this).html().match(/<input.*?">/g)[0];
            };
        };
    });

    $('[contenteditable=true]')
        .focus(function() {
            $(this).data("initialText", $(this).html());
            if ( $(this).html().match(/<input.*?">/g)[0] ) {
                $comInput = $(this).html().match(/<input.*?">/g)[0];
            };
        })
        .blur(function() {
            if (! $(this).html().includes("<input")) {
                $(this).html($(this).html() + $comInput);
            };

            if ($(this).data("initialText") !== $(this).html()) {
                $(this).children('input').val($(this).html().replace(/<input.*?">/g, '').replace('<br>', '').trim());
            };
        });

    $('.showGoldenAnnotation').unbind('click').click(function(){
        //loadingScreen();
        $button = $(this);
        if ($button.hasClass('editGoldenAndSystem')) {
            $goldenLabel = '.goldenAndSystemLabel';
            $title = "Salvar golden e sistema ao mesmo tempo";
        } else {
            $goldenLabel = '.goldenLabel';
            $title = "Salvar golden";
        };
        $button.siblings('.cancelChanges').click();
        $button.parent().parent().next('.getAnnotation').children('.ud').val('ud1');
        $button.parent().parent().next('.getAnnotation').ajaxSubmit({
            url: '/api/getAnnotation',
            type: 'POST',
            success: function(data){
                $button.html("<span class='glyphicon glyphicon-ok'></span> " + $button.siblings($goldenLabel).val().split('</i>')[1]);
                $button.siblings('.cancelChanges').show();
                $button.attr('title', $title);
                $button.removeClass('btn-default').addClass('btn-success').removeClass('showGoldenAnnotation').addClass('hideGoldenAnnotation');
                $button.parents('.panel-body').find('.annotationGolden').html(data['annotationUd1']);
                $button.parents('.panel-body').find('.annotationGolden').show();
                atualizar();
            },
        });
    });
    
    $('.hideGoldenAnnotation').unbind('click').click(function(){
        loadingScreen();
        $button = $(this);
        if ($button.hasClass('editGoldenAndSystem')) {
            $button.parent().parent().parent().find('.sendGoldenAnnotation').children("[name=goldenAndSystem]").val('1');
            $goldenLabel = '.goldenAndSystemLabel';
            $title = "Editar golden e sistema ao mesmo tempo";
        } else {
            $button.parent().parent().parent().find('.sendGoldenAnnotation').children("[name=goldenAndSystem]").val('0');            
            $goldenLabel = '.goldenLabel';
            $title = "Mostrar golden";
        };
        $button.parent().parent().parent().find('.sendGoldenAnnotation').ajaxSubmit({
            url: "/api/sendAnnotation",
            type: 'POST',
            success: function(data){
                if (data['change']){
                    $button.parents('.sentence').children('.modification').html(
                    '<div class="alert alert-success" role="alert">Alteração no GOLDEN realizada com sucesso dia ' + data['data'] + '</div>'
                    )
                };
                if (data['attention']){
                    $button.parents('.sentence').children('.modification').append(data['attention'])
                };
                $button.siblings('.cancelChanges').hide();
                $button.attr('title', $title);
                $button.html($button.siblings($goldenLabel).val());
                $button.removeClass('btn-success').addClass('btn-default').removeClass('hideGoldenAnnotation').addClass('showGoldenAnnotation');
                $button.parents('.panel-body').find('.annotationGolden').hide();
                $button.parent().parent().parent().parent().get(0).scrollIntoView();
                atualizar();
            },
        });
    });

    $('.showSystemAnnotation').unbind('click').click(function(){
        //loadingScreen();
        $button = $(this);
        $button.siblings('.cancelChanges').click();
        $button.parent().parent().next('.getAnnotation').children('.ud').val('ud2');
        $button.parent().parent().next('.getAnnotation').ajaxSubmit({
            url: '/api/getAnnotation',
            type: 'POST',
            success: function(data){
                $button.siblings('.cancelChanges').show();
                $button.html("<span class='glyphicon glyphicon-ok'></span>" + $button.siblings('.systemLabel').val().split('</i>')[1]);
                $button.attr('title', 'Salvar sistema');
                $button.removeClass('btn-default').addClass('btn-success').removeClass('showSystemAnnotation').addClass('hideSystemAnnotation');
                $button.parents('.panel-body').find('.annotationSystem').html(data['annotationUd2']);
                $button.parents('.panel-body').find('.annotationSystem').show();
                atualizar();
            },
        });
    });
    
    $('.hideSystemAnnotation').unbind('click').click(function(){
        loadingScreen();
        $button = $(this);
        $button.parent().parent().parent().find('.sendSystemAnnotation').ajaxSubmit({
            url: '/api/sendAnnotation',
            type: 'POST',
            success: function(data){
                if (data['change']){
                    $button.parents('.sentence').children('.modification').html(
                    '<div class="alert alert-danger" role="alert">Alteração no <font color="red"><b>SISTEMA</b></font> realizada com sucesso dia ' + data['data'] + '</div>'
                    )};
                $button.siblings('.cancelChanges').hide();
                $button.attr('title', 'Mostrar sistema');
                $button.html($button.siblings('.systemLabel').val());
                $button.removeClass('btn-success').addClass('btn-default').removeClass('hideSystemAnnotation').addClass('showSystemAnnotation');
                $button.parents('.panel-body').find('.annotationSystem').hide();
                $button.parent().parent().parent().parent().get(0).scrollIntoView();
                atualizar();
            },
        });
    });

    $('.cancelChanges').unbind('click').click(function(){
        loadingScreen();
        $(this).parents('.panel-body').find('.annotationSystem').hide();
        $(this).parents('.panel-body').find('.annotationGolden').hide();
        $(this).hide();
        $(this).siblings('.hideSystemAnnotation').removeClass('btn-success').addClass('btn-default').removeClass('hideSystemAnnotation').addClass('showSystemAnnotation').html($(this).siblings('.systemLabel').val()).attr('title', 'Mostrar sistema');
        $(this).siblings('.hideGoldenAnnotation').removeClass('btn-success').addClass('btn-default').removeClass('hideGoldenAnnotation').addClass('showGoldenAnnotation').html($(this).siblings('.goldenLabel').val()).attr('title', 'Mostrar golden');
        $(this).siblings('.editGoldenAndSystem').html($(this).siblings('.goldenAndSystemLabel').val()).attr('title', 'Editar golden e sistema ao mesmo tempo');
        $(this).parent().parent().parent().parent().get(0).scrollIntoView();
        atualizar();
    });

    $('.quickSendAnnotation').unbind("click").click(function(){
        loadingScreen();
        $button = $(this);
        $button.next('.quickFormAnnotation').ajaxSubmit({
            url: '/api/sendAnnotation',
            type: 'POST',
            success: function(data){
                if (data['change']){
                    $button.parents('.sentence').children('.modification').html(
                    '<div class="alert alert-success" role="alert">Alteração realizada com sucesso dia ' + data['data'] + '</div>'
                    );
                    $button.removeClass('btn-default').addClass('btn-success');
                    $button.html('Salvo');
                    $button.siblings('.hideSystemAnnotation').click();
                    $button.siblings('.hideGoldenAnnotation').click();
                    atualizar();
                };                
            },
        });
    });

    $('.opt').click(function(){
        $('.uploadOption').hide();
        $div = $(this).attr('name');
        $('.' + $div).show();
    });

    endLoadingScreen();
  
};

function loadingScreen(){
    $('#loading-bg').show();
    $('#loading-image-nobg').show();
    $("title").text("Carregando | " + $("title").text());
}

function endLoadingScreen(){
    $('#loading-bg').hide();
    $('#loading-image-nobg').hide();
    if ($("title").text().indexOf("Carregando | ") !== -1){
        $("title").text($("title").text().split("Carregando | ")[1]);
    }
};

$(window).on('beforeunload', function() {
    loadingScreen();
});

$(window).on('unload', function() {
    endLoadingScreen();
});

$(window).ready(function(){
    endLoadingScreen();
});

var userLang = navigator.language || navigator.userLanguage;

$(document).ready(function(){

    atualizar();

    $('.sobreCorpus').blur(function(){
        loadingScreen();
        if (!$(".sobreCorpus").text()){
            $(".sobreCorpus").text(">");
        };
        $.ajax({
            url: "/api/changeAbout",
            method: "POST",
            data: {
                c: $("#c").val(),
                about: $('.sobreCorpus').html()
            },
            success: function(data){
                $('.sobreCorpus').html(data['html']);
                atualizar();
            }
        });
    })

    $('.refreshTables').click(function(){
        loadingScreen();
        $('.tables').hide();
        $.ajax({
            url: "/api/refreshTables",
            method: "POST",
            data: {
                c: $('#c').val()
            },
            success: function(){
                window.location.href = "/corpus?c=" + $('#c').val();
            }
        });
    });

    $('.cristianMarneffeToggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        tipo = $(this).attr("tipo");
        $.ajax({
            url:"/api/cristianMarneffe",
            method:"POST",
            data: {
                c: $('#c').val(),
                tipo: tipo,
            },
            success: function(data){
                $('#cristianMarneffe').html('<h3>Cristian-Marneffe (' + tipo + ')</h3>' + data['html'] + "</div>");
                $('#cristianMarneffe').show();
                atualizar();
            }
        })
    });

    $('.errorLogToggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        $.ajax({
            url:"/api/getErrors",
            method:"POST",
            data: {
                c: $('#c').val(),
                exceptions: "Sent",
                fromZero: false,
            },
            success: function(data){
                $('#errorLog').html('<h3>Erros de validação</h3>' + data['html'] + "</div>");
                $('#errorLog').show();
                atualizar();
            }
        })
    });

    $('.errorValidarUDToggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        $.ajax({
            url:"/api/getErrorsValidarUD",
            method:"POST",
            data: {
                c: $('#c').val(),
            },
            success: function(data){
                $('#errorValidarUD').html('<h3>Erros de validação</h3>' + data['html'] + "</div>");
                $('#errorValidarUD').show();
                atualizar();
            }
        })
    });

    $('.trainFile').on('change', function(){
        loadingScreen();
        $button = $('#trainFile');//$('[data-id=trainFile]');
        $corpus = $('#trainFile').val();
        $.ajax({
            url:"/api/getErrors",
            method:"POST",
            data: {
                c: $button.val(),
                fromZero: true,
            },
            success: function(data){
                if (data['html']){
                    $('.uploadOption').hide();
                    $('.correctErrors').html("<h3>Corrija os erros em " + $corpus + " para continuar</h3>" + data['html'] + "<button name='optTrainSys' class='btn btn-default opt'>Voltar ao treinamento</button>");
                    $('.correctErrors').show();
                    $('#trainFile').selectpicker('val', ' -- escolha uma opção -- ');
                    $('#submitTrain').removeClass('btn-success').addClass('btn-default');
                    $('#submitTrain').prop("disabled", true);
                } else {
                    $('#submitTrain').removeClass('btn-default').addClass('btn-success');
                    $('#submitTrain').prop("disabled", false);
                }
                atualizar();                
            }
        });
    });

    $('.filterDeleteSystem').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterDeleteSystem').val(),
                tipo: 'delete',
            },
            success: function(data){
                $('.deleteSystemCorpora').html(data['html']);
            },
        }); 
    });

    $('.filterDeleteGolden').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterDeleteGolden').val(),
                tipo: 'deleteGolden',
            },
            success: function(data){
                $('.deleteGoldenCorpora').html(data['html']);
            },
        }); 
    });

    $('.filterAvailableCorpora').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterAvailableCorpora').val(),
                tipo: 'available',
            },
            success: function(data){
                $('.availableCorpora').html(data['html']);
            },
        }); 
    });

    $('.filterOnlyGolden').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterOnlyGolden').val(),
                tipo: 'onlyGolden',
            },
            success: function(data){
                $('.onlyGolden').html(data['html']);
            },
        }); 
    });

    $('.filterTrainingCorpora').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterTrainingCorpora').val(),
                tipo: 'training',
            },
            success: function(data){
                $('.trainingCorpora').html(data['html']);
            },
        }); 
    });

    $('.filterSuccessCorpora').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterSuccessCorpora').val(),
                tipo: 'success',
            },
            success: function(data){
                $('.successCorpora').html(data['html']);
            },
        }); 
    });

    if (window.location.href.includes('log')){
        $('#log').stop().animate({scrollTop: $('#log')[0].scrollHeight}, 800);
    };

    $('.tables-toggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        $div = $(this).attr('name');
        $.ajax({
            url:"/api/getTables",
            method:"POST",
            data: {
                table: $div,
                ud1: $('#ud1').val(),
                ud2: $('#ud2').val(),
                c: $('#c').val()
            },
            success: function(data){
                $('#' + $div).children('.panel-body').html(data['html']);
                $('#' + $div).show();
                atualizar();
            },
        });
    });

    $('.catSent').click(function(e){
        $('tr').css('background-color', 'inherit');
        $(this).parents('tr').css('background-color', 'yellow');
        loadingScreen();
        $button = $(this);
        e.preventDefault();
        $.ajax({
            url:"/api/getCatSents",
            method:"POST",
            data: {
                c: $button.attr('c'),
                tipo: $button.attr('tipo'),
                deprel: $button.attr('deprel'),
                coluna: $button.attr('coluna'),
            },
            success: function(data){
                $('.catSentences').html(data['html']);
                atualizar();
                window.scrollTo(0,0);
            },
        });
    });

    $('#back-to-top').click(function () {
        $('body,html').animate({scrollTop:0}, 1000, 'swing');  
    });

    $(document).scroll(function(){
        if ($(this).scrollTop() > 54) {
            $('#back-to-top').fadeIn();
        } else {
            $('#back-to-top').fadeOut();
        };
    });

});
