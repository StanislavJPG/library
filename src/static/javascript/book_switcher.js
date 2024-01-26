function incrementNum() {
        var urlParams = new URLSearchParams(window.location.search);
        var currentNum = parseInt(urlParams.get('num'));
        var newNum = currentNum + 1;

        urlParams.set('num', newNum);
        document.getElementById('Next').textContent;

        var newUrl = window.location.pathname + '?' + urlParams.toString();
        window.history.pushState({ path: newUrl }, '', newUrl);

        window.location.replace(newUrl);
    }
function incrementNum_back() {
        var urlParams = new URLSearchParams(window.location.search);
        var currentNum = parseInt(urlParams.get('num'));
        var newNum = currentNum - 1;

        urlParams.set('num', newNum);
        document.getElementById('Back').textContent;

        var newUrl = window.location.pathname + '?' + urlParams.toString();
        window.history.pushState({ path: newUrl }, '', newUrl);

        window.location.replace(newUrl);
}
 var pdfEmbed = document.getElementById('pdfEmbed');

    function toggleFullscreen() {
      if (pdfEmbed.requestFullscreen) {
        pdfEmbed.requestFullscreen();
      } else if (pdfEmbed.mozRequestFullScreen) {
        pdfEmbed.mozRequestFullScreen();
      } else if (pdfEmbed.webkitRequestFullscreen) {
        pdfEmbed.webkitRequestFullscreen();
      } else if (pdfEmbed.msRequestFullscreen) {
        pdfEmbed.msRequestFullscreen();
      }
    }

function confirmRating(url) {
      const ratingInputs = document.querySelectorAll('.rating');

      ratingInputs.forEach(ratingInput => {
          if (ratingInput.checked) {
              ratingValue = ratingInput.value;
          }
      });

      var isRating = confirm(`Оцінити цю книгу на ${ratingValue}?`);

      if (isRating) {

          const ratingUrl = '/save_rating_to_database';
          const data = {
              "current_book_url": url,
              "user_rating": ratingValue,
              }

          const ratingOptions = {
              method: 'POST',
              headers: {
                  'accept': 'application/json',
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify(data),
          };

          fetch(ratingUrl, ratingOptions)
              .then(response => {
                  if (response.ok) {
                      alert(`Дякуємо за оцінку!`);
                      location.reload();
                  } else {
                      alert(`Failed to confirm rating. Status: ${response.status}`);
                  }
              })
        }
    }
