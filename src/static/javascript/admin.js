function BookCreate(id=null, title, description, url, url_orig, page) {
    const Url = `/api/admin_panel/create_book?page=${page}`;
    if (id === null) {
        const data = {
              "title": title,
              "description": description,
              "url": url,
              "url_orig": url_orig,
              }
    }
    else {
        const data = {
              "id": id,
              "title": title,
              "description": description,
              "url": url,
              "url_orig": url_orig,
              }
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
                    alert('422');
                });
            } else if (response.status === 400) {
                alert('Запитів на створення цієї книги немає.');
            } else {
                alert('Створено.');
                location.reload();
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
}
