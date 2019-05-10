$(document).ready(function () {
    var image = new Image();
    numColsToCut = 4;
    numRowsToCut = 4;
    image.onload = cutImageInTiles;
    image.src = "puzzle10.jpeg";

    var firstStep = true;

    var originalImagePieces = [];
    var currentImagePieces = [];
    var temporaryArray = [];
    var index = 0;

    var firstTileClicked;
    var secondTileClicked;
    var topPosFir = 0;
    var leftPosFir = 0;
    var topPosSec = 0;
    var leftPosSec = 0;


    function cutImageInTiles() {
        widthOfOnePiece = image.naturalWidth / numColsToCut;
        heightOfOnePiece = image.naturalHeight / numRowsToCut;
        for (var x = 0; x < numColsToCut; ++x) {
            for (var y = 0; y < numRowsToCut; ++y) {
                var canvas = document.createElement('canvas');
                canvas.width = widthOfOnePiece;
                canvas.height = heightOfOnePiece;
                var context = canvas.getContext('2d');
                console.log("sx: " + x * widthOfOnePiece);
                console.log("sy: " + y * heightOfOnePiece);
                context.drawImage(image, y * heightOfOnePiece, x * widthOfOnePiece, widthOfOnePiece, heightOfOnePiece, 0, 0, canvas.width, canvas.height);
                originalImagePieces.push(canvas.toDataURL());
            }
        }

        var puzzleDiv = $("#puzzleDiv")[0];
        puzzleDiv.style.height = numRowsToCut * heightOfOnePiece + 8 + "px";
        puzzleDiv.style.width = numColsToCut * widthOfOnePiece + 8 + "px";

        currentImagePieces = originalImagePieces.slice();
        removeAllElementsFromPuzzleDiv();
        addImagesOnScreen(currentImagePieces);
    }

    function addImagesOnScreen() {
        console.log("Index: " + index)
        if (index < currentImagePieces.length) {
            let imageToAdd = new Image();
            indexID = originalImagePieces.findIndex(x => x === currentImagePieces[index]);
            $(imageToAdd).attr("id", indexID);
            $(imageToAdd).addClass("tile");
            // imageToAdd.style.display = "inline-block";
            imageToAdd.onload = function () {
                puzzleDiv.appendChild(imageToAdd);
                imageToAdd.style.marginLeft = "1px";
                imageToAdd.style.marginRight = "1px";
                imageToAdd.style.marginTop = "-1px";
                imageToAdd.style.marginBottom = "-1px";
                index++;

                setTimeout(function () {
                    addImagesOnScreen();
                }, 20);
            };
            imageToAdd.onerror = function () {
                console.log("Failed to load image");
            };

            imageToAdd.src = currentImagePieces[index];
        }
    }


    $('body').on('click', 'img', function () {
        if (firstStep) {
            firstStep = false;

            firstTileClicked = $(this).attr('id');
            topPosFir = parseInt($(this).css('top'));
            leftPosFir = parseInt($(this).css('left'));

        } else {
            firstStep = true;

            secondTileClicked = $(this).attr('id');
            topPosSec = parseInt($(this).css('top'));
            leftPosSec = parseInt($(this).css('left'));

            swapElements($('#' + firstTileClicked)[0], $('#' + secondTileClicked)[0]);
        }

    });

    function swapElements(el1, el2) {
        let parent = $("#puzzleDiv");
        var nodes = Array.prototype.slice.call(parent.children());
        console.log("Index 1: " + nodes.indexOf(el1));
        console.log("Index 1: " + nodes.indexOf(el2));

        let prev1 = el1.previousSibling;
        let prev2 = el2.previousSibling;

        prev1.after(el2);
        prev2.after(el1);

        // el2.nextSibling === el1 ? el1.parentNode.insertBefore(el2, el1.nextSibling) : el1.parentNode.insertBefore(el2, el1);
    }

    function removeAllElementsFromPuzzleDiv() {
        index = 0;
        var puzzleDiv = $("#puzzleDiv")[0];
        while (puzzleDiv.firstChild) {
            puzzleDiv.removeChild(puzzleDiv.firstChild);
        }
    }

    $("#shuffle_btn").click(function () {

        var currentIndex = originalImagePieces.length, temporaryValue, randomIndex;
        console.log("Current index:" + originalImagePieces.length);
        temporaryArray = originalImagePieces.slice();
        // While there remain elements to shuffle...
        while (0 !== currentIndex) {
            // Pick a remaining element...
            randomIndex = Math.floor(Math.random() * currentIndex);
            currentIndex -= 1;
            // And swap it with the current element.
            temporaryValue = temporaryArray[currentIndex];
            temporaryArray[currentIndex] = temporaryArray[randomIndex];
            temporaryArray[randomIndex] = temporaryValue;
            console.log("Current index:" + originalImagePieces.length);
        }
        currentImagePieces = temporaryArray.slice();
        removeAllElementsFromPuzzleDiv();
        addImagesOnScreen();
    });

    $("#show_original_btn").click(function () {
        currentImagePieces = originalImagePieces.slice();
        removeAllElementsFromPuzzleDiv();
        addImagesOnScreen();
    });

});
