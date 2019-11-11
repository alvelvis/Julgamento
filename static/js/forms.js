function scrollToAnchor(aid){
    var aTag = $(aid);
    $('html,body').animate({scrollTop: aTag.offset().top},'slow');
};

function apagarCorpus(corpus){
    if (window.confirm('Tem certeza de que deseja apagar o corpus "' + corpus + '"?')) {
        window.location = '/cancelTrain?c=' + corpus + '&delete=True&callback=upload&golden=' + $(".deleteGoldenToo").is(":checked");
    };
};

function atualizar(){

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
            },
        })
    });

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
                $('.branch').selectpicker('refresh');
                $('.repoCommit').selectpicker('refresh');
                atualizar();
            }
        });
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

    $('.drag').click(function(){
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
        loadingScreen();
        $button = $(this);
        $button.siblings('.cancelChanges').click();
        $button.parent().parent().next('.getAnnotation').children('.ud').val('ud1');
        $button.parent().parent().next('.getAnnotation').ajaxSubmit({
            url: '/api/getAnnotation',
            type: 'POST',
            success: function(data){
                $button.html("<span class='glyphicon glyphicon-ok'></span> " + $button.siblings('.goldenLabel').val().split('</i>')[1]);
                $button.siblings('.cancelChanges').show();
                $button.attr('title', 'Salvar golden');
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
        $button.parent().parent().parent().find('.sendGoldenAnnotation').ajaxSubmit({
            url: '/api/sendAnnotation',
            type: 'POST',
            success: function(data){
                console.log(data['attention']);
                if (data['change']){
                    $button.parents('.sentence').append(
                    '<div class="alert alert-success" role="alert">Alteração realizada com sucesso dia ' + data['data'] + '</div>'
                    )
                };
                if (data['attention']){
                    $button.parents('.sentence').append(data['attention'])
                };
                $button.siblings('.cancelChanges').hide();
                $button.attr('title', 'Mostrar golden');
                $button.html($button.siblings('.goldenLabel').val());
                $button.removeClass('btn-success').addClass('btn-default').removeClass('hideGoldenAnnotation').addClass('showGoldenAnnotation');
                $button.parents('.panel-body').find('.annotationGolden').hide();
                $button.parent().parent().parent().parent().get(0).scrollIntoView();
                atualizar();
            },
        });
    });

    $('.showSystemAnnotation').unbind('click').click(function(){
        loadingScreen();
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
                    $button.parents('.sentence').append(
                    '<div class="alert alert-success" role="alert">Alteração realizada com sucesso no sistema dia ' + data['data'] + '</div>'
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
                    $button.parents('.sentence').append(
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
}

function endLoadingScreen(){
    $('#loading-bg').hide();
    $('#loading-image-nobg').hide();
}

$(window).on('beforeunload', function() {
    $('#loading-bg').show();
    $('#loading-image').show();
});

$(window).on('unload', function() {
    $('#loading-bg').hide();
    $('#loading-image').hide();
});

$(window).ready(function(){
    $('#loading-bg').hide();
    $('#loading-image').hide();
});

$(document).ready(function(){

    atualizar();

    $('.sobreCorpus').blur(function(){
        loadingScreen();
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
                window.location.href = "/corpus";
            }
        });
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
