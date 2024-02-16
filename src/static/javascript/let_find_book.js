function letAdminFindBook(title, image) {
    const Url = "/books/let_find";
    const data = {
          "title": title,
          "image": image
          }

    const Options = {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      };

          fetch(Url, Options)
        .then(response => {
            if (response.status === 422) {
                response.json().then(data => {
                    alert('Помилка 422.');
                });
            } else if (response.status === 409) {
                alert('Запит на пошук вже надісланий користувачами\nМи в пошуках цієї книги!');
            } else {
                alert('Дякую! Наші модератори вже займаються цією проблемою :)');
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
}