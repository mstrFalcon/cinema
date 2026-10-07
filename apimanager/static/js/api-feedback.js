(() => {
    document.querySelectorAll('.api-feedback').forEach((card) => {
        const retry = card.querySelector('.api-feedback__retry');
        const label = card.querySelector('.api-feedback__retry-label');
        const status = card.querySelector('.api-feedback__status');
        if (!retry || !label || !status) return;

        const initialLabel = label.textContent;
        let loading = false;

        const reset = () => {
            loading = false;
            retry.removeAttribute('aria-disabled');
            retry.removeAttribute('aria-busy');
            label.textContent = initialLabel;
            status.textContent = '';
        };

        retry.addEventListener('click', (event) => {
            if (event.defaultPrevented || event.button !== 0 || event.ctrlKey
                || event.metaKey || event.shiftKey || event.altKey) return;

            event.preventDefault();
            if (loading) return;

            loading = true;
            retry.setAttribute('aria-disabled', 'true');
            retry.setAttribute('aria-busy', 'true');
            label.textContent = 'Загрузка…';
            status.textContent = 'Загружаем данные. Пожалуйста, подождите…';

            // Два кадра дают браузеру показать индикатор перед переходом.
            window.requestAnimationFrame(() => {
                window.requestAnimationFrame(() => {
                    window.location.assign(retry.href);
                });
            });
        });

        // При возврате из кеша истории кнопка снова доступна.
        window.addEventListener('pageshow', (event) => {
            if (event.persisted) reset();
        });
    });
})();
