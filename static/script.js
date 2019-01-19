function setNavigationPill(linkId) {
    let navLinks = document.querySelectorAll(".nav-link");
    let linkCount = navLinks.length;
    for (let i=0; i < linkCount; i++) {
        let classList = navLinks[i].classList;
        if (navLinks[i].id == linkId) classList.add("active");
        else classList.remove("active");
    }
}

function getWeather(weatherArea) {
    fetch("/weather")
        .then(response => {return response.json();})
        .then(json => {
            weatherArea.innerHTML = `
            <div class="row">
                <div class="col-2">Messzeit</div>
                <div class="col-10">${json["timestamp_display"]}</div>
            </div>
            <div class="row">
                <div class="col-2">Wetter</div>
                <div class="col-4">${json["weather"]}</div>
                <div class="col-4">${json["weather_desc"] }</div>
                <div class="col-2"><img src="http://openweathermap.org/img/w/${json["icon"]}.png"> </div>
            </div>
            <div class="row">
                <div class="col-2">Temperatur</div>
                <div class="col-10">${json["temp"]} (Min: ${json["temp_min"]}, Max: ${json["temp_max"]})</div>
            </div>`;
        })
        .catch(error => {
            console.error('error fetching /weather:', error);
            weatherArea.innerHTML = "Wetterdienst konnte nicht erreicht werden";
        });

}



//---- location ---------------------------------------------------

function closeAllLists(input, elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    let x = document.getElementsByClassName("autocomplete-items");
    for (let i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != input) {
            x[i].parentNode.removeChild(x[i]);
        }
    }
}

function closeAutocompleteOnClick() {
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

function onAlpha2CdChanged(alpha2cdField, cityField) {
    console.log("onAlpha2CdChanged called");
    console.log(alpha2cdField);
    if (alpha2cdField.value.length > 0) {
        cityField.value = "";
        cityField.disabled = false;
    } else {
        cityField.value = "Bitte zuerst Land auswählen";
        cityField.disabled = true;
    }
}

function createCountrySuggestionDiv(countryField, alpha2cdField, parent, country, cityField) {
    let suggestionDiv = document.createElement("div");
    suggestionDiv.innerText = country["country_name"] + " (" + country["alpha2_cd"] + ")";

    let hiddenCountry = document.createElement("input");
    hiddenCountry.setAttribute("type", "hidden");
    hiddenCountry.setAttribute("value", country["country_name"]);
    suggestionDiv.appendChild(hiddenCountry);

    let hiddenAlpha = document.createElement("input");
    hiddenAlpha.setAttribute("type", "hidden");
    hiddenAlpha.setAttribute("value", country["alpha2_cd"]);
    suggestionDiv.appendChild(hiddenAlpha);


    parent.appendChild(suggestionDiv);
    suggestionDiv.addEventListener("click", function(e) {
        countryField.value = this.getElementsByTagName("input")[0].value;
        alpha2cdField.value = this.getElementsByTagName("input")[1].value;
        onAlpha2CdChanged(alpha2cdField, cityField);
        closeAllLists();
    });
}

function setCountryAutocomplete(countryField, alpha2Field, cityField) {
    countryField.addEventListener("input", function () {
        let countryParam = "?input=" + countryField.value;

        let url1 = "/alpha2_cd" + countryParam;
        console.log("fetch: " + url1);
        fetch(url1)
        .then(response => {return response.json();})
        .then(json => {
            let alpha2 = json["alpha2_cd"];
            console.log("answer: " + json);
            if(alpha2.length > 0) { // country is already filled in
                alpha2Field.value = alpha2;
                onAlpha2CdChanged(alpha2Field);
                closeAllLists();
            } else { // country not entirely filled in, show dropdown list
                let url2 = "/countries" + countryParam;
                fetch(url2)
                .then(response => {return response.json();})
                .then(json => {
                    let countries = json["suggestions"];
                    if (countries.length > 0) {
                        let a = document.createElement("div");
                        a.setAttribute("id", this.id + "autocomplete-list");
                        a.setAttribute("class", "autocomplete-items");
                        /*append the DIV element as a child of the autocomplete container:*/
                        document.getElementById("countryAutocomplete").appendChild(a);
                        countries.forEach( country => {
                            createCountrySuggestionDiv(countryField, alpha2Field, a, country, cityField);
                        });
                    }
                });
            }
        });
    });
}

function onLatLongChanged(latField, longField, setLocationButton) {
    console.trace();
    console.log()
    setLocationButton.disabled = latField.value.length == 0 || longField.value.length == 0;
}

function createCitySuggestionDiv(cityField, latField, longField, parent, city, setLocationButton) {
    let suggestionDiv = document.createElement("div");
    suggestionDiv.innerText = city["city"];

    let hiddenCity = document.createElement("input");
    hiddenCity.setAttribute("type", "hidden");
    hiddenCity.setAttribute("value", city["city"]);
    suggestionDiv.appendChild(hiddenCity);

    let hiddenLat = document.createElement("input");
    hiddenLat.setAttribute("type", "hidden");
    hiddenLat.setAttribute("value", city["lat"]);
    suggestionDiv.appendChild(hiddenLat);

    let hiddenLong = document.createElement("input");
    hiddenLong.setAttribute("type", "hidden");
    hiddenLong.setAttribute("value", city["long"]);
    suggestionDiv.appendChild(hiddenLong);

    parent.appendChild(suggestionDiv);
    suggestionDiv.addEventListener("click", function(e) {
        cityField.value = this.getElementsByTagName("input")[0].value;
        latField.value = this.getElementsByTagName("input")[1].value;
        longField.value = this.getElementsByTagName("input")[2].value;
        onLatLongChanged(latField, longField, setLocationButton);
        closeAllLists();
    });
}

function setCityAutocomplete(alpha2Field, cityField, latField, longField, setLocationButton) {
    cityField.addEventListener("input", function () {
        let countryInputParam = "?input=" + cityField.value + "&country=" + alpha2Field.value;

        let url1 = "/city" + countryInputParam;
        console.log("fetch: " + url1);
        fetch(url1)
        .then(response => {return response.json();})
        .then(json => {
            if(json["found"]) { // city is already filled in
                let city = json["city"];
                latField.value = city["lat"];
                longField.value = city["long"];
                onLatLongChanged(latField, longField, setLocationButton);
                closeAllLists();
            } else { // country not entirely filled in, show dropdown list
                let url2 = "/cities" + countryInputParam;
                fetch(url2)
                .then(response => {return response.json();})
                .then(json => {
                    let cities = json["suggestions"];
                    if (cities.length > 0) {
                        let a = document.createElement("div");
                        a.setAttribute("id", this.id + "autocomplete-list");
                        a.setAttribute("class", "autocomplete-items");
                        /*append the DIV element as a child of the autocomplete container:*/
                        document.getElementById("cityAutocomplete").appendChild(a);
                        cities.forEach(function (city) {
                            createCitySuggestionDiv(cityField, latField, longField, a, city, setLocationButton);
                        });
                    }
                });
            }
        });
    });
}

function getRecommendedActivities(mentalEnergy, physicalEnergy, timeAtDisposal, activityDiv) {
    console.log("getRecommendetActivities called:");
    console.log(mentalEnergy);
    console.log(physicalEnergy);
    console.log(timeAtDisposal);
    console.log(activityDiv);

    let url = "/recommended_activities?mentalEnergy=" + mentalEnergy +
            "&physicalEnergy=" + physicalEnergy +
            "&timeAtDisposal=" + timeAtDisposal;
    console.log("call " + url);
    fetch(url)
        .then(function (response) {
            console.log(response);
            return response.json();
        })
        .then(function(json) {
            console.log("json: " + json);
            let act = json["recommended_activities"];
            if (act.length == 0) {
                activityDiv.innerText = "Es konnten keine passenden Einträge gefunden werden"
            } else {
                let ol = document.createElement("ol");
                act.forEach(function (activity) {
                    let li = document.createElement("li");
                    li.innerText = activity["activity"] + " (" + activity["score"] + "%)";
                    ol.appendChild(li);
                });
                activityDiv.appendChild(ol);
            }
        });
}

function preventDefaults(event) {
    event.preventDefault();
    event.stopPropagation();
}

function highlight(area) {
    area.classList.add("highlight");
}

function unhighlight(area) {
    area.classList.remove("highlight");
}

function handleFiles(files) {
    // files is not an array but a FileList object
  ([...files]).forEach(file => {

  })
}

function handleDrop(event) {
    let dt = event.dataTransfer;
    let files = dt.files;
    handleFiles(files);
}
//---- diary ---------------------------------------------------
/* thanks to https://www.smashingmagazine.com/2018/01/drag-drop-file-uploader-vanilla-js/ */
function createDragAndDropArea(area) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, preventDefaults)
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        area.addEventListener(eventName, e => {highlight(area)})
    });

    ['dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, e => {unhighlight(area)})
    });

}