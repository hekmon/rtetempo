# RTE Tempo

Cette extension vous permet d'obtenir les infos [Tempo](https://www.services-rte.com/fr/visualisez-les-donnees-publiees-par-rte/calendrier-des-offres-de-fourniture-de-type-tempo.html) directement depuis RTE.

Elle intègre dans Home Assistant plusieurs éléments:

* un calendrier sur un an (avec la possibilité de passer les évènements en heures réèlles)
* des capteurs de la couleur actuelle et celle du lendemain en texte et en emoji
* des capteurs comptants les jours passés et futurs de chaque couleurs
* des capteurs permettant de connaître la date et l'heure (et donc le temps restant) du prochain changement de couleur mais aussi du cycle en cours
* des capteurs liés aux heures creuses pour faciliter les automatisations

### Exemples

[Service et Capteurs](https://github.com/hekmon/rtetempo/raw/v1.2.0/res/rtetempo_svc.png) & [Calendrier](https://github.com/hekmon/rtetempo/raw/v1.2.0/res/rtetempo_calendar.png)

## Installation

Certaines capteurs sont de type `enum` afin de faciliter leur utilisation dans des automatisations. Cette fonctionnalitée de Home Assistant ayant été introduite à la version `2023.1.0`, assurez-vous de ne pas avoir un Home Assistant plus ancien avant l'installation de cette intégration.

### Créer une application d'accès à l'API de RTE

Les données sont récupérées directement depuis l'[API de RTE](https://data.rte-france.com/) et son accès nécessite la création d'une application afin d'obtenir des jetons d'authentification.

Voici comment faire :

* [Créez un compte](https://data.rte-france.com/create_account) sur la plateforme.
* Recherchez `Tempo Like Supply Contract` dans le catalogue d'API (présent dans la catégorie [Consommation](https://data.rte-france.com/catalog/consumption)) et cliquez sur `Découvrir l'API`.
* Une fois sur la page de l'API Tempo, sélectionnez `Abonnez-vous à l'API` et créez une application (ou sélectionnez une existante que vous utilisez déjà pour votre Home Assistant).
* Une fois l'application créée et l'API Tempo associée, récupérez les informations d'authentification de votre [application](https://data.rte-france.com/group/guest/apps): `ID Client` et `ID Secret`.

### Installation de l'intégration dans Home Assistant

Téléchargez l'intégration depuis la page des [releases](https://github.com/hekmon/rtetempo/releases) et décompressez le dossier `custom_components/rtetempo` dans votre dossier de configuration de Home Assistant. Vous devez obtenir: `/chemin/vers/dossier/de/configuration/homeassistant/custom_components/rtetempo`.

Redémarrez votre Home Assistant.

### Configuration de l'intégration

Une fois l'intégration installée, rendez-vous dans la page des intégrations d'home assistant et recherchez `RTE Tempo`. L'assistant d'installation vous demandera l'`ID Client` et l'`ID Secret` de votre application précédemment créée.

## Exemples de cartes (lovelace)

* Couleur du jour et du lendemain ([rendu 1](https://github.com/hekmon/rtetempo/raw/v1.2.0/res/lovelace_colors_1.png) [rendu 2](https://github.com/hekmon/rtetempo/raw/v1.2.0/res/lovelace_colors_2.png), [code](https://github.com/hekmon/rtetempo/blob/v1.2.0/res/tempo.yaml))
* Nombre de jours restants sur le cycle ([rendu](https://github.com/hekmon/rtetempo/raw/v1.2.0/res/lovelace_cycle.png), [code](https://github.com/hekmon/rtetempo/blob/v1.2.0/res/tempo_cycle.yaml))
