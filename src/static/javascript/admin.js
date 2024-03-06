function BookCreate(id, title, image, description, url, url_orig, page) {
    const Url = `/api/admin_panel/create_book?page=${page}`;
    const data = {
          "id": id,
          "title": title,
          "image": "https://" + image,
          "description": description,
          "url": url,
          "url_orig": url_orig,
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
            } else {
                alert('Створено.');
                location.reload();
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
}
