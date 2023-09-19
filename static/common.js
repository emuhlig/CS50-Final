// Select HTML elements
const onoff = document.getElementById("onoff");
const cmode = document.getElementById("cmode");
const briVal = document.getElementById("briVal");
const hueVal = document.getElementById("hueVal");
const satVal = document.getElementById("satVal");
const tempVal = document.getElementById("tempVal");
const briSlider = document.getElementById("brightness");
const hueSlider = document.getElementById("hue");
const satSlider = document.getElementById("saturation");
const tempSlider = document.getElementById("temp");
const sliders = [briSlider, hueSlider, satSlider, tempSlider];
const hueLabel = document.getElementById("hueLabel");
const satLabel = document.getElementById("satLabel");
const tempLabel = document.getElementById("tempLabel");

// Set minimum and maximum command values based on light API
// Note: Hue doesn't accept bri=0, would require logic to power off
const briMin = 1;
const briMax = 254;
const hueMin = 0;
const hueMax = 65535;
const satMin = 0;
const satMax = 254;

// Set slider ranges using common conventions
const briSliderMin = 1;
const briSliderMax = 100;
const hueSliderMin = 0;
const hueSliderMax = 360;
const satSliderMin = 0;
const satSliderMax = 100;

// Configure slider limits and initial positions 
briSlider.min = briSliderMin;
briSlider.max = briSliderMax;
briSlider.value = scale(brightness, briMin, briMax, briSliderMin, briSliderMax);
hueSlider.min = hueSliderMin;
hueSlider.max = hueSliderMax;
hueSlider.value = scale(hue, hueMin, hueMax, hueSliderMin, hueSliderMax);
satSlider.min = satSliderMin;
satSlider.max = satSliderMax;
satSlider.value = scale(saturation, satMin, satMax, satSliderMin, satSliderMax);

// Convert mirek scale to standard kelvin
tempSlider.min = Math.round(1e6 / tempMax);
tempSlider.max = Math.round(1e6 / tempMin);
tempSlider.value = Math.round(1e6 / temp);

// Reduce granularity of any larger sliders to 100 steps
for (let i = 0; i < sliders.length; i++) {
    const range = sliders[i].max - sliders[i].min;
    if (range >= 150) {
        sliders[i].step = Math.round(range / 100);
    }
}

// Initialize slider readouts and switch positions
briVal.innerHTML = `${briSlider.value}%`;
hueVal.innerHTML = `${hueSlider.value}°`;
satVal.innerHTML = `${satSlider.value}%`;
tempVal.innerHTML = `${tempSlider.value} K`;

// Initialize page background
drawBG();
modeDisplay();

// Show or hide UI elements depending on color mode
function modeDisplay() {
    if (cmode.checked) {
        hueSlider.style.display = "inline-block";
        hueLabel.style.display = "inline-block";
        hueVal.style.display = "inline-block";
        satSlider.style.display = "inline-block";
        satLabel.style.display = "inline-block";
        satVal.style.display = "inline-block";
        tempSlider.style.display = "none";
        tempLabel.style.display = "none";
        tempVal.style.display = "none";
    } else {
        hueSlider.style.display = "none";
        hueLabel.style.display = "none";
        hueVal.style.display = "none";
        satSlider.style.display = "none";
        satLabel.style.display = "none";
        satVal.style.display = "none";
        tempSlider.style.display = "inline-block";
        tempLabel.style.display = "inline-block";
        tempVal.style.display = "inline-block";
    }
}

// Convert value in a range to the corresponding position within a new range
function scale(val, valMin, valMax, newMin = 0, newMax = 100) {
    const valRange = valMax - valMin;
    const newRange = newMax - newMin;
    const relPos = (val - valMin) / valRange;
    const newVal = newMin + relPos * newRange;
    return Math.round(newVal);
}

// Limit the rate of commands being sent to the light while ensuring final input is registered
let lastInputTime = 0;
let lastCommandTime = 0;
function throttle() {
    lastInputTime = Date.now();
    timeSinceLastCommand = Date.now() - lastCommandTime;
    if (timeSinceLastCommand > 250) {
        lastCommandTime = Date.now();
        command(payload);
    } else {
        setTimeout(function() {
            timeSinceLastInput = Date.now() - lastInputTime;
            if (timeSinceLastInput >= 200) {
                lastCommandTime = Date.now();
                command(payload);
            }
        }, 200);
    }
}

// Draw page background gradient based on current group state
function drawBG() {
    let h = hueSlider.valueAsNumber;
    let s = satSlider.valueAsNumber;
    let lightness = 0;
    if (onoff.checked) {
        document.body.style.color = "black";
        if (cmode.checked) {
            lightness = scale((satMax - saturation), satMin, satMax, 50, 100);
        } else {
            h = 33; // Approximate hue of incandescent (deg)
            s = scale(temp, tempMin, tempMax, 0, 100);
            lightness = scale((tempMax - temp), tempMin, tempMax, 62, 100);
        }
    } else {
        document.body.style.color = "white";
    }
    let hsl = `hsl(${h}, ${s}%, ${lightness}%)`;
    let glowPos = scale(brightness, briMin, briMax, 0, 50);
    let outerPos = 10 + 1.5 * glowPos;
    let gradient = `radial-gradient(circle, ${hsl} ${glowPos}%, #333 ${outerPos}%)`;
    document.body.style.backgroundImage = gradient;
}

// Brightness slider
briSlider.addEventListener("input", function(event) {
    brightness = scale(briSlider.valueAsNumber, briSliderMin, briSliderMax, briMin, briMax);
    briVal.innerHTML = `${briSlider.value}%`;
    if (onoff.checked) {
        payload = {"bri": brightness};
        throttle();
    }
});

// Hue slider
hueSlider.addEventListener("input", function(event) {
    hue = scale(hueSlider.valueAsNumber, hueSliderMin, hueSliderMax, hueMin, hueMax);
    hueVal.innerHTML = `${hueSlider.value}°`;
    if (onoff.checked && cmode.checked) {
        payload = {"hue": hue};
        throttle();
    }
});

// Saturation slider
satSlider.addEventListener("input", function(event) {
    saturation = scale(satSlider.valueAsNumber, satSliderMin, satSliderMax, satMin, satMax);
    satVal.innerHTML = `${satSlider.value}%`;
    if (onoff.checked && cmode.checked) {
        payload = {"sat": saturation};
        throttle();
    }
});

// Temperature slider
tempSlider.addEventListener("input", function(event) {
    temp = Math.round(1e6 / tempSlider.valueAsNumber);
    tempVal.innerHTML = `${tempSlider.value} K`;
    if (onoff.checked && !cmode.checked) {
        payload = {"ct": temp};
        throttle();
    }
});

// Power switch
onoff.addEventListener("input", function(event) {
    if (onoff.checked) {
        payload = {
            "on": true,
            "bri": brightness,
        };
        if (cmode.checked) {
            payload["hue"] = hue;
            payload["sat"] = saturation;
        } else {
            payload["ct"] = temp;
        }
    } else {
        payload = {"on": false};
    }
    throttle();
});

// Color mode switch
cmode.addEventListener("input", function(event) {
    modeDisplay();
    if (cmode.checked) {
        payload = {
            "hue": hue,
            "sat": saturation,
        };
    } else {
        payload = {"ct": temp};
    }
    if (onoff.checked) {
        throttle();
    }
});