# HueFX
#### [Video Demo](https://youtu.be/tC_DCfLa26A)
#### Description:
HueFX is a smart-light controller for Philips Hue that offers functionality beyond the official Philips app. This project was inspired by features that are available in the app for LIFX, a different brand of smart lighting. The ultimate goal is to combine the superior aspects of each brand into one comprehensive smart light system.

HueFX takes the form of a web application utilizing the [Flask framework](https://flask.palletsprojects.com/en/2.3.x/quickstart/). Communication with Hue devices is made possible by the [Philips Hue API](<https://developers.meethue.com>), while the frontend design utilizes [Bootstrap 5.1](<http://getbootstrap.com/docs/5.1/>).

### Important Note:
HueFX is a personal project. This application doesn't offer any means to discover or pair with a new Philips Hue system. Using this code on your own system will require a Hue developer account and additional configuration steps described in the [Hue developer onboarding](<https://developers.meethue.com/develop/get-started-2/>).

### Features:

##### Sign-up and Login:
The site features a basic user account feature. You must create an account to use the app. After creating an account, you have the ability to log in, change your password, and log out. Although the user profiles don't currently serve a practical purpose, this feature could be used to store information for the hub pairing process and restrict access to the lights if the app were hosted online.

##### Home Page:
The home page of HueFX displays a dynamic list of groups that have been established on the hub, as well as the lights contained within those groups. At the top of the page there is also a special group containing all lights known to the hub. Clicking any of these items will bring you to the corresponding light controller.

##### Light Controller:
The controller page provides direct and synchronized control of light parameters. Upon loading the page, the user interface (buttons, sliders, and background color) are set to match the current state of the light. For a group of lights, the parameters (brightness, hue, saturation, and temperature) are calculated as averages of the lights that are currently powered on. If all lights are off, the sliders are set to the last known state of the light(s).

Interacting with a button or slider while a light is powered on will immediately trigger requests to change the light. The UI will be updated in near real-time to reflect the change after the hub reports that the request was successful. Unlike the official Philips app, you are free to adjust parameters while a light is off. Upon powering it back on, it will simply reflect the final position of the sliders. This is especially useful when you've been in the dark and want to make sure the lights are dim at first.

When controlling a group of lights, the modified parameter will be applied uniformly to all lights within the group without affecting the other parameters. For example, if the lights within a group are set to various colors and you adjust the brightness of the group, the color choices will not be lost. However, modifying the group color controls will immediately unify the lights to a single color.

The color mode selection switch toggles between the two schemes of the light while remembering your color setpoints, a distinct advantage over the Philips app. For example, you are able to toggle between a bright blue and warm incandescent bulb. The Philips app instead keeps a light stationary in colorwheel space, thus blue always becomes a cool white when toggling between modes.

#### Technical Details:
###### Python backend `app.py` and `helpers.py`
These files configure the application and handle the various app routes. The primary routes (home, light, and group) are very simple. First, a request for the state of the hub is made using the `lookup` function. This information is then passed into the HTML render template that gets delivered to the client.

The `lookup` function is used to request information from the hub via GET method. This requires an API key that was currently hard-coded after following the Hue Developer onboarding steps. The hub will provide a response in JSON format which simply becomes this function's return value.

The `control` route acts a middleman between the client-side JavaScript and the hub. The server collects request data via POST method and passes it into the `sendCommand` function. The outcome of sendCommand is processed and the corresponding updates and/or errors are returned to the client.

The `sendCommand` function operates in a very similar manner to the `lookup` function. Using an API key and the PUT method, the payload parameter is delivered to the hub in JSON format. The hub provides a response which is then returned to the caller.

Finally, the `controlGroup` route is nearly identical to the `control` route. The Hue API requires a few differences for controlling a group instead of a light.

###### Frontend `light.html`, `group.html`, `controller.html`, and `common.js`
The light and group controller pages are very similar and will be discussed as one topic. The UI elements (buttons, sliders, and labels) are contained within a form, which has been extracted to its own file controller.html. The remaining code is JavaScript for handling changes to the form and exchanging data with the server. The light.html and group.html pages contain certain unique scripts, but the majority of functionality is extracted to common.js.

The initial values and limits of the UI controls are set based on the state of the light, which was passed along by the server upon page load, as well as hard-coded setpoints from the Hue API docs. The background of the page is drawn to mimic the state of the light using functions developed through trial and error.

It's important to limit the rate of commands sent to the hub. First, the UI sliders are capped to a maximum number of steps (e.g. 0-360 is reduced to 100 steps of 3.6 each). Furthermore, any change registered by an event listener is throttled to maintain a steady rate of commands being sent to the hub. This means that even if a user moves a UI element especially quickly, the hub won't be overloaded by commands. This `throttle` function also includes a closing timeout to ensure the final state set by the user is captured and sent to the hub.

Finally, the `command` function collects a payload from the controller form and sends it to the server via POST method. This is handled as explained above in the `app.py` section, after which the response is returned to the script. The updates described by this response are processed such that the UI stays in sync with the hub. The resulting light state is used to redraw the page background and adjust any buttons or sliders as necessary.