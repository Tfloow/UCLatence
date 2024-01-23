# UCLouvain website DownDetector

- [UCLouvain website DownDetector](#uclouvain-website-downdetector)
  - [Introduction](#introduction)
  - [How does it work ?](#how-does-it-work-)
  - [How to run it ?](#how-to-run-it-)
    - [Explanation of the steps](#explanation-of-the-steps)
  - [Roadmap](#roadmap)
  - [Documentation](#documentation)
  - [License](#license)

Test the app [here](https://uclouvaindown-ed3979a045e6.herokuapp.com/)

## Introduction

This website is displaying which website or service related to the UCLouvain is down at the moment.

You can find the list of all currently track services in this [json](services.json).

## How does it work ?

![Homepage](doc/img/image.png)![Alt text](image.png)

Here is the control panel where every website is displayed.

I am using Flask to run the website and handle all interaction between the user and the website.

To know if a service is down simply go to the `/<service>` on the website.

I am tracking and storing the last status in the JSON and only doing request every 5 minutes.

## How to run it ?

First, make sure to get the latest version of python (I am using 3.12). then follow these steps:

1. `git clone git@github.com:Tfloow/UCLouvainDown.git` (*or fork it*)
2. `pip install -r requirements.txt`
3. `flask run --host=0.0.0.0`

### Explanation of the steps

1. Clone the repo so you can get the code
2. In the main directory, install all needed dependencies and the correct version without hassle in one command
3. Run the app. It will host locally on your pc and you can access it through other devices connected on the same network as your pc

## Roadmap

- [x] Working pages
- [x] Home Page with links to other sub-pages
- [ ] A nice and clear home page with all current status
- [x] Deployed locally
- [x] Deployed globally 
- [x] Tracking downtime 
- [x] User button to report if a website is down
- [x] Database that collect persistent data about outage
- [ ] Proper database

## Documentation

You can find the documentation and have a better understanding of what is going under the hood by reading [this](doc/doc.md). (*Please, open an issue with the tag "doc" to add any comments or when you need more information about a specific point of the doc*).

## License

This work is protected under the [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). For the favicon, I used the UCLouvain's logo and 2 images that doesn't belong to me but to their rightful owner (*Check compliance with the license*).