class CountrySearch {
    constructor(selectId, inputId, resultsId, options = {}) {
        this.select = document.getElementById(selectId) || document.querySelector(`select[name="${selectId}"]`);
        this.input = document.getElementById(inputId);
        this.results = document.getElementById(resultsId);
        this.countries = [];
        this.onSelect = options.onSelect || null;
        this.themeColor = options.themeColor || '#F37021';

        if (this.select && this.input && this.results) {
            this.init();
        }
    }

    async init() {

        Array.from(this.select.options).forEach(opt => {
            if (opt.value && opt.value !== "") {
                this.countries.push({
                    code: opt.value,
                    name: opt.textContent.toUpperCase()
                });
            }
        });


        this.select.style.display = 'none';


        this.input.addEventListener('input', () => this.filter());
        this.input.addEventListener('focus', () => {
            if (this.input.value.length > 0) this.filter();
        });


        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.results.contains(e.target)) {
                this.results.style.display = 'none';
            }
        });


        if (!document.getElementById('country-search-styles')) {
            const style = document.createElement('style');
            style.id = 'country-search-styles';
            style.innerHTML = `
                .search-results-container {
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: #1f242d;
                    border: 1px solid #2a2f3a;
                    max-height: 250px;
                    overflow-y: auto;
                    z-index: 9999;
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                    display: none;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                }
                .country-search-item {
                    padding: 12px 15px;
                    cursor: pointer;
                    color: #fff;
                    font-size: 0.9rem;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                    transition: all 0.2s;
                    text-align: left;
                }
                .country-search-item:last-child { border-bottom: none; }
                .country-search-item:hover {
                    background: ${this.themeColor} !important;
                    padding-left: 20px;
                }
            `;
            document.head.appendChild(style);
        }
    }

    filter() {
        const val = this.input.value.toUpperCase();
        this.results.innerHTML = '';
        
        if (val.length === 0) {
            this.results.style.display = 'none';
            return;
        }

        const filtered = this.countries.filter(c => c.name.includes(val)).slice(0, 10);

        if (filtered.length > 0) {
            this.results.style.display = 'block';
            filtered.forEach(country => {
                const div = document.createElement('div');
                div.className = 'country-search-item';
                div.textContent = country.name;
                div.onclick = () => {
                    this.input.value = country.name;
                    this.select.value = country.code;
                    this.results.style.display = 'none';
                    

                    const event = new Event('change', { bubbles: true });
                    this.select.dispatchEvent(event);

                    if (this.onSelect) this.onSelect(country);
                };
                this.results.appendChild(div);
            });
        } else {
            this.results.style.display = 'none';
        }
    }
}
