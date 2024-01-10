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