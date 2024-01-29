// Variável de traduções resetada porque houve grande reformulação nos nomes "golden"/"sistema", e essa reformulação ainda está em teste.
var translations = {
    
};

$('.filterSentences').click(function(){
    $('.filterSentencesDiv').slideToggle();
});

$('.filterThisSentenceBtn').click(function(){
    if ($('#filterSentencesInput').val().split("|").indexOf($(this).attr('sent_id')) == -1) {
        $('#filterSentencesInput').val($('#filterSentencesInput').val() + ($('#filterSentencesInput').val().length ? "|" : "") + $(this).attr('sent_id'));
        $('.filterSentencesButton').click();
    }
})

$('.filterSentencesButton').click(function(){
    $('.sentenceDiv').each(function(i, div){
        if ($('#filterSentencesInput').val().length && $(div).find('.sent_id').text().match($('#filterSentencesInput').val())) {
            $(div).hide();
        } else {
            $(div).show();
        }
    })
});

function updateTranslation(){

    $('.translateHtml').each(function(){
        if (translations[$(this).html()]) {
            if (userLang == "pt-BR" || userLang == "pt-PT") {
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
            if (userLang == "pt-BR" || userLang == "pt-PT") {
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
            if (userLang == "pt-BR" || userLang == "pt-PT") {
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
            if (userLang == "pt-BR" || userLang == "pt-PT") {
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
        window.location = '/cancelTrain?c=' + corpus + '&delete=True&callback=upload&first=' + $(".deleteFirstToo").is(":checked");
    };
};

function apagarcorpusFirst(corpus){
    if (window.confirm('Tem certeza de que deseja apagar o corpus "' + corpus + '"?')) {
        window.location = '/api/deleteFirst?c=' + corpus;
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

    $('.showfirstAnnotation').unbind('click').click(function(){
        //loadingScreen();
        $button = $(this);
        if ($button.hasClass('editfirstAndsecond')) {
            $firstLabel = '.firstAndsecondLabel';
            $title = "Salvar corpus principal e secundário ao mesmo tempo";
        } else {
            $firstLabel = '.firstLabel';
            $title = "Salvar principal";
        };
        $button.siblings('.cancelChanges').click();
        $button.parent().parent().next('.getAnnotation').children('.ud').val('ud1');
        $button.parent().parent().next('.getAnnotation').ajaxSubmit({
            url: '/api/getAnnotation',
            type: 'POST',
            success: function(data){
                $button.html("<span class='glyphicon glyphicon-ok'></span> " + $button.siblings($firstLabel).val().split(' ')[1]);
                $button.siblings('.cancelChanges').show();
                $button.attr('title', $title);
                $button.removeClass('btn-default').addClass('btn-success').removeClass('showfirstAnnotation').addClass('hidefirstAnnotation');
                $button.parents('.panel-body').find('.annotationfirst').html(data['annotationUd1']);
                $button.parents('.panel-body').find('.annotationfirst').show();
                atualizar();
            },
        });
    });
    
    $('.hidefirstAnnotation').unbind('click').click(function(){
        loadingScreen();
        $button = $(this);
        if ($button.hasClass('editfirstAndsecond')) {
            $button.parent().parent().parent().find('.sendfirstAnnotation').children("[name=firstAndsecond]").val('1');
            $firstLabel = '.firstAndsecondLabel';
            $title = "Editar corpus principal e secundário ao mesmo tempo";
        } else {
            $button.parent().parent().parent().find('.sendfirstAnnotation').children("[name=firstAndsecond]").val('0');            
            $firstLabel = '.firstLabel';
            $title = "Mostrar principal";
        };
        $button.parent().parent().parent().find('.sendfirstAnnotation').ajaxSubmit({
            url: "/api/sendAnnotation",
            type: 'POST',
            success: function(data){
                if (data['change']){
                    $button.parent().parent().find('.alreadyEdited').text('!');
                    $button.parents('.sentence').children('.modification').html(
                    '<div class="alert alert-success" role="alert">Alteração no PRINCIPAL realizada com sucesso dia ' + data['data'] + '</div>'
                    )
                };
                if (data['attention']){
                    $button.parents('.sentence').children('.modification').append(data['attention'])
                };
                $button.siblings('.cancelChanges').hide();
                $button.attr('title', $title);
                $button.html($button.siblings($firstLabel).val());
                $button.removeClass('btn-success').addClass('btn-default').removeClass('hidefirstAnnotation').addClass('showfirstAnnotation');
                $button.parents('.panel-body').find('.annotationfirst').hide();
                $button.parent().parent().parent().parent().get(0).scrollIntoView();
                atualizar();
            },
        });
    });

    $('.showTokenIds').unbind('click').click(function(){
        $(this).parent().siblings('.header').children('.tokenIds').slideToggle();
        $(this).parent().siblings('.header').children('.text').slideToggle();
        $(this).toggleClass('btn-default').toggleClass('btn-success');
    });

    $('.token').unbind('mouseenter').on('mouseenter', function(){
        $(this).parent().children('#token_id').html($(this).attr('token_id'))
    })

    $('.showsecondAnnotation').unbind('click').click(function(){
        //loadingScreen();
        $button = $(this);
        $button.siblings('.cancelChanges').click();
        $button.parent().parent().next('.getAnnotation').children('.ud').val('ud2');
        $button.parent().parent().next('.getAnnotation').ajaxSubmit({
            url: '/api/getAnnotation',
            type: 'POST',
            success: function(data){
                $button.siblings('.cancelChanges').show();
                $button.html("<span class='glyphicon glyphicon-ok'></span>" + $button.siblings('.secondLabel').val().split(' ')[1]);
                $button.attr('title', 'Salvar secundário');
                $button.removeClass('btn-default').addClass('btn-success').removeClass('showsecondAnnotation').addClass('hidesecondAnnotation');
                $button.parents('.panel-body').find('.annotationsecond').html(data['annotationUd2']);
                $button.parents('.panel-body').find('.annotationsecond').show();
                atualizar();
            },
        });
    });

    $('.showPhrases').unbind('click').click(function(){
        $button = $(this);
        $.ajax({
            url: "/api/getPhrases",
            method: "POST",
            data: {
                sent_id: $button.attr('sent_id'),
                c: $("#c").val()
            },
            success: function(data){
                $button.parent().siblings('.header').children('.phrases').html(data['html']);
                $button.parent().siblings('.header').children('.phrases').slideToggle();
                $button.toggleClass('btn-default').toggleClass('btn-success');
            }
        });
    });
    
    $('.hidesecondAnnotation').unbind('click').click(function(){
        loadingScreen();
        $button = $(this);
        $button.parent().parent().parent().find('.sendsecondAnnotation').ajaxSubmit({
            url: '/api/sendAnnotation',
            type: 'POST',
            success: function(data){
                if (data['change']){
                    $button.parents('.sentence').children('.modification').html(
                    '<div class="alert alert-danger" role="alert">Alteração no <font color="red"><b>SECUNDÁRIO</b></font> realizada com sucesso dia ' + data['data'] + '</div>'
                    )};
                $button.siblings('.cancelChanges').hide();
                $button.attr('title', 'Mostrar secundário');
                $button.html($button.siblings('.secondLabel').val());
                $button.removeClass('btn-success').addClass('btn-default').removeClass('hidesecondAnnotation').addClass('showsecondAnnotation');
                $button.parents('.panel-body').find('.annotationsecond').hide();
                $button.parent().parent().parent().parent().get(0).scrollIntoView();
                atualizar();
            },
        });
    });

    $('.cancelChanges').unbind('click').click(function(){
        loadingScreen();
        $(this).parents('.panel-body').find('.annotationsecond').hide();
        $(this).parents('.panel-body').find('.annotationfirst').hide();
        $(this).hide();
        $(this).siblings('.hidesecondAnnotation').removeClass('btn-success').addClass('btn-default').removeClass('hidesecondAnnotation').addClass('showsecondAnnotation').html($(this).siblings('.secondLabel').val()).attr('title', 'Mostrar secundário');
        $(this).siblings('.hidefirstAnnotation').removeClass('btn-success').addClass('btn-default').removeClass('hidefirstAnnotation').addClass('showfirstAnnotation').html($(this).siblings('.firstLabel').val()).attr('title', 'Mostrar principal');
        $(this).siblings('.editfirstAndsecond').html($(this).siblings('.firstAndsecondLabel').val()).attr('title', 'Editar corpus principal e secundário ao mesmo tempo');
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
                    $button.siblings('.hidesecondAnnotation').click();
                    $button.siblings('.hidefirstAnnotation').click();
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
            $(".sobreCorpus").text("Editar descrição");
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

    $('.inconsistent_ngramsToggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        tipo = $(this).attr("tipo");
        $.ajax({
            url:"/api/inconsistent_ngrams",
            method:"POST",
            data: {
                c: $('#c').val(),
                tipo: tipo,
            },
            success: function(data){
                $('#inconsistent_ngrams').html('<h3 class="translateHtml">N-grams inconsistentes (' + tipo + ')</h3>' + data['html'] + "</div>");
                $('#inconsistent_ngrams').show();
                atualizar();
            }
        })
    });

    $('.errorUDToggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        $.ajax({
            url:"/api/getErrorsUD",
            method:"POST",
            data: {
                c: $('#c').val(),
                exceptions: "Sent",
                fromZero: false,
            },
            success: function(data){
                $('#errorUD').html('<h3 class="translateHtml">Detecção de erros segundo o script UD</h3>O script de erros é obtido do repositório UniversalDependencies/tools no Github<hr>' + data['html'] + "</div>");
                $('#errorUD').show();
                atualizar();
            }
        })
    });

    $('.errorETToggle').click(function(){
        loadingScreen();
        $('.tables').hide();
        $.ajax({
            url:"/api/getErrorsET",
            method:"POST",
            data: {
                c: $('#c').val(),
            },
            success: function(data){
                $('#errorET').html('<h3 class="translateHtml">Detecção de erros segundo o script da ET</h3>O script de erros pode ser editado no arquivo Julgamento/validar_UD.txt<hr>' + data['html'] + "</div>");
                $('#errorET').show();
                atualizar();
            }
        })
    });

    $('.trainFile').on('change', function(){
        loadingScreen();
        $button = $('#trainFile');//$('[data-id=trainFile]');
        $corpus = $('#trainFile').val();
        $.ajax({
            url:"/api/getErrorsUD",
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

    $('.filterdeleteSecond').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterdeleteSecond').val(),
                tipo: 'delete',
            },
            success: function(data){
                $('.deleteSecondCorpora').html(data['html']);
            },
        }); 
    });

    $('.filterdeleteFirst').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterdeleteFirst').val(),
                tipo: 'deleteFirst',
            },
            success: function(data){
                $('.deleteFirstCorpora').html(data['html']);
            },
        }); 
    });

    
    $('.filterCorporaFeatures').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterCorporaFeatures').val(),
                tipo: 'features',
            },
            success: function(data){
                $('.seeCorporaFeatures').html(data['html']);
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

    $('.filterOnlyfirst').keyup(function(){
        $.ajax({
            url:"/api/filterCorpora",
            method:"POST",
            data: {
                filtro: $('.filterOnlyfirst').val(),
                tipo: 'onlyfirst',
            },
            success: function(data){
                $('.onlyfirst').html(data['html']);
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
        $('.tables').hide();
        $div = $(this).attr('name');
        matrix_col = ""
        if ($div == "matrix") { 
            matrix_col = window.prompt("Coluna (ex: upos, deprel, deps, etc.)") 
            if (!matrix_col) {
                return
            }
        }
        loadingScreen();
        $.ajax({
            url:"/api/getTables",
            method:"POST",
            data: {
                table: $div,
                ud1: $('#ud1').val(),
                ud2: $('#ud2').val(),
                c: $('#c').val(),
                matrix_col: matrix_col
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
