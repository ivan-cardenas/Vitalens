
    
    mapboxgl.accessToken = 'pk.eyJ1IjoiY3lnbnVzMjYiLCJhIjoiY2s5Z2MzeWVvMGx3NTNtbzRnbGtsOXl6biJ9.8SLdJuFQzuN-s4OlHbwzLg';
    const map = new mapboxgl.Map({
        container: 'map', // container ID
        center: [6.7, 52.38],
        pitch: 60,
        // starting position [lng, lat]. Note that lat must be set between -90 and 90
        zoom:  10// starting zoom
        });    
    