# Cahier des charges — Marketplace multi-vendeurs (Guinée)

### Type Wildberries / Ozon — Backend FastAPI + Frontend moderne

\---

## 1\. Contexte et vision

Créer une marketplace e-commerce multi-vendeurs adaptée au marché guinéen (Conakry en priorité, extension régionale ensuite), permettant à des vendeurs tiers (boutiques, artisans, importateurs) de vendre leurs produits à des acheteurs guinéens, avec paiement mobile money et livraison locale.

**Contraintes marché spécifiques à intégrer dès la conception :**

* Connectivité mobile souvent limitée (3G, data coûteuse) → frontend léger, images optimisées, PWA installable.
* Paiement dominant : Mobile Money (Orange Money, MTN MoMo/Momo) + paiement à la livraison (cash on delivery) très répandu.
* Adresses postales peu structurées → géolocalisation, points de repère textuels, quartiers/communes plutôt qu'adresses formelles.
* Devise : Franc guinéen (GNF), pas de décimales à gérer (montants entiers).
* Langue : français (interface), avec possibilité d'extension future vers le poular, le soussou, le malinké.
* Logistique : réseau de livraison à Conakry à construire (livreurs indépendants ou partenaires), livraison inter-villes plus complexe.

\---

## 2\. Objectifs du produit

1. Permettre à des vendeurs indépendants de créer une boutique, publier des produits, gérer leurs stocks et commandes.
2. Permettre aux acheteurs de rechercher, comparer, acheter et suivre leurs commandes facilement, même avec une connexion faible.
3. Centraliser le paiement (mobile money + cash à la livraison) et la logistique.
4. Offrir à l'administrateur une visibilité et un contrôle complets (modération, commissions, litiges).

\---

## 3\. Rôles utilisateurs

|Rôle|Description|
|-|-|
|**Acheteur**|Parcourt le catalogue, achète, suit ses commandes, laisse des avis|
|**Vendeur**|Gère sa boutique, ses produits, son stock, ses commandes, ses revenus|
|**Livreur** (phase 2)|Reçoit des missions de livraison, met à jour le statut de livraison|
|**Administrateur**|Modère les vendeurs/produits, gère les commissions, supervise les litiges, accède aux statistiques globales|

\---

## 4\. Périmètre fonctionnel

### 4.1 MVP (Phase 1 — priorité de développement)

**Côté acheteur**

* Inscription / connexion (téléphone + OTP ou email)
* Parcours du catalogue par catégories
* Recherche avec filtres (prix, catégorie, vendeur, disponibilité)
* Fiche produit (photos, description, prix, stock, avis)
* Panier multi-vendeurs (un panier peut contenir des produits de plusieurs boutiques → split automatique en plusieurs commandes à la validation)
* Tunnel de commande : choix adresse/zone de livraison, mode de paiement, récapitulatif
* Suivi de commande (statuts : en attente, confirmée, en préparation, expédiée, livrée, annulée)
* Historique des commandes
* Avis et notes produits/vendeurs après livraison

**Côté vendeur**

* Inscription vendeur + validation admin
* Tableau de bord vendeur (commandes, revenus, stock)
* CRUD produits (nom, catégorie, prix, stock, photos, description)
* Gestion des commandes reçues (accepter, préparer, marquer expédié)
* Visualisation des paiements/commissions

**Côté admin**

* Validation/modération des vendeurs
* Modération des produits (signalés, non conformes)
* Gestion des catégories
* Configuration des commissions par catégorie/vendeur
* Vue globale des commandes et litiges
* Statistiques (ventes, top produits, top vendeurs)

**Paiement (MVP)**

* Intégration **NimbaPay** — moyen de paiement principal dès le lancement
* Paiement à la livraison (cash) — filet de sécurité en parallèle, tant que l'adoption de NimbaPay monte en puissance
* Orange Money / MTN MoMo — repoussés en option phase 2 si besoin (NimbaPay étant justement conçu pour interconnecter ces portefeuilles mobiles avec les banques, il couvre déjà une bonne partie de ce besoin)

**Infrastructure MVP**

* Authentification sécurisée (JWT), rôles et permissions
* Upload et stockage d'images (produits) avec compression automatique
* Notifications (email et/ou SMS) sur les changements de statut de commande

### 4.2 Phase 2 (post-MVP)

* Système de livraison avec livreurs affectés, tracking temps réel
* Chat acheteur ↔ vendeur
* Système de promotions/coupons, ventes flash
* Recommandations personnalisées (produits similaires, "souvent achetés ensemble")
* Application mobile native (ou PWA avancée avec notifications push)
* Multi-devises / extension régionale (Sénégal, Côte d'Ivoire, etc.)
* Programme de fidélité
* Support multilingue (poular, soussou, malinké)

\---

## 5\. Architecture technique proposée

### 5.1 Stack

* **Backend** : FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.0 (async) ou SQLModel
* **Base de données** : PostgreSQL (transactionnel, robuste, extensible avec pgvector si recommandation IA en phase 2)
* **Cache / files d'attente** : Redis (cache, sessions, files pour notifications/emails async)
* **Frontend** : Vue/Vuetify (choisi un Framework adapté) avec rendu hybride SSR/SSG pour le SEO catalogue + PWA (installable, fonctionnement partiel hors-ligne)
* **Stockage fichiers** : S3-compatible (ex. MinIO en local/self-hosted, ou un provider cloud) pour les images produits
* **Authentification** : JWT (access + refresh token), hashing bcrypt/argon2
* **Paiement** : intégration API Orange Money + MTN MoMo (webhooks de confirmation), mode cash-on-delivery natif
* **Tâches asynchrones** : Celery ou ARQ + Redis (notifications, traitement d'images, relances de paiement)
* **Conteneurisation** : Docker + docker-compose pour le développement, déploiement cible à définir (VPS local ou cloud)

### 5.2 Modules backend (découpage FastAPI)

```
app/
├── core/            # config, sécurité, dépendances communes
├── auth/            # inscription, connexion, JWT, OTP
├── users/           # profils acheteurs
├── vendors/         # boutiques, validation, tableau de bord vendeur
├── catalog/         # produits, catégories, recherche, filtres
├── cart/            # panier multi-vendeurs
├── orders/          # commandes, sous-commandes par vendeur, statuts
├── payments/        # orange money, mtn momo, cash on delivery
├── delivery/        # zones de livraison, frais (MVP simple ; livreurs en phase 2)
├── reviews/         # avis produits/vendeurs
├── notifications/   # email/SMS, événements
├── admin/           # modération, commissions, statistiques
└── common/          # schémas partagés, utilitaires
```

### 5.3 Modèle de données (entités principales)

* **User** (id, téléphone, email, mot de passe hashé, rôle, statut)
* **Vendor** (id, user\_id, nom boutique, statut validation, zone, commission\_rate)
* **Category** (id, nom, parent\_id pour hiérarchie)
* **Product** (id, vendor\_id, category\_id, nom, description, prix, stock, images\[], statut)
* **CartItem** (id, user\_id, product\_id, quantité)
* **Order** (id, user\_id, statut global, adresse/zone livraison, mode paiement, total)
* **SubOrder** (id, order\_id, vendor\_id, statut, montant, commission)
* **OrderItem** (id, sub\_order\_id, product\_id, quantité, prix unitaire)
* **Payment** (id, order\_id, méthode, statut, référence transaction externe)
* **Review** (id, product\_id, user\_id, note, commentaire)
* **DeliveryZone** (id, commune/quartier, frais de livraison, délai estimé)

\---

## 6\. Exigences non fonctionnelles

* **Performance** : temps de réponse API < 300ms sur les endpoints catalogue ; images servies en formats optimisés (WebP) avec plusieurs résolutions.
* **Résilience réseau** : le frontend doit gérer gracieusement les connexions lentes/instables (retry automatique, chargement progressif, mode dégradé).
* **Sécurité** : validation stricte des entrées (Pydantic), protection CSRF/XSS côté frontend, rate limiting sur l'authentification, chiffrement des données sensibles, webhooks de paiement signés/vérifiés.
* **Scalabilité** : architecture modulaire permettant d'ajouter des vendeurs et catégories sans refonte.
* **Observabilité** : logs structurés, monitoring des erreurs de paiement (point critique en Guinée).

\---

## 7\. Points de vigilance particuliers

1. **Paiement NimbaPay** : NimbaPay est le système national de paiement instantané de la Guinée, lancé le 22 juillet 2026 sous l'égide de la BCRG et mis en œuvre par la Guinéenne de Monétique (GuiM), sur une infrastructure technique Mojaloop. **Ce n'est pas un portefeuille électronique en soi, mais un rail d'interopérabilité** qui relie en temps réel banques, émetteurs de monnaie électronique et institutions de microfinance — un peu comme Pix au Brésil ou UPI en Inde. Étant très récemment lancé, une documentation API publique pour les marchands/développeurs n'était pas trouvable au moment de la rédaction de ce document ; il faudra :

   * Contacter la Guinéenne de Monétique (GuiM) ou la BCRG pour obtenir l'accès marchand et la documentation technique (spécifications API, sandbox, identifiants) ;
   * Concevoir dès maintenant le module `payments/` de façon **abstraite** (interface `PaymentProvider` avec une implémentation `NimbaPayProvider` isolée), afin de brancher l'intégration réelle dès que les specs seront obtenues, sans revoir l'architecture ;
   * Prévoir un mode "cash on delivery" comme filet de sécurité en attendant/à côté de l'intégration NimbaPay, le temps que l'adoption monte en puissance côté utilisateurs et vendeurs.
2. **Livraison** : au MVP, la livraison peut être gérée manuellement par les vendeurs eux-mêmes (auto-livraison) plutôt que par une flotte centralisée — évite de complexifier le MVP.
3. **Vérification vendeurs** : processus de validation manuelle par l'admin pour limiter la fraude au démarrage (peu de vendeurs au début).
4. **Split de commande multi-vendeurs** : bien clarifier dès la conception de la base de données que Order ≠ SubOrder (une commande acheteur peut se décomposer en plusieurs sous-commandes, une par vendeur, chacune avec son propre statut et paiement).

\---

## 8\. Plan de développement par étapes

1. **Socle technique** : setup FastAPI + PostgreSQL + Docker, authentification JWT, structure de projet
2. **Catalogue \& vendeurs** : CRUD produits/catégories, inscription et validation vendeur
3. **Panier \& commande** : logique panier multi-vendeurs, split en sous-commandes
4. **Paiement** : interface abstraite `PaymentProvider` + implémentation cash on delivery d'abord, puis intégration NimbaPay dès que l'accès marchand/documentation est obtenu auprès de GuiM
5. **Tableaux de bord** : vendeur puis admin
6. **Frontend acheteur complet** (Next.js/PWA)
7. **Notifications** (email/SMS)
8. **Tests, durcissement sécurité, préparation déploiement**

\---

## 9\. Prompt Claude Code — à utiliser pour démarrer le développement

```
Tu es un développeur senior full-stack. Nous allons construire ensemble une
marketplace e-commerce multi-vendeurs pour le marché guinéen (type Wildberries/Ozon),
en suivant le cahier des charges ci-joint (cahier\_des\_charges\_marketplace\_guinee.md).

CONTEXTE
- Backend : FastAPI (Python 3.12+), SQLAlchemy 2.0 async, PostgreSQL, Redis
- Frontend : Next.js (React), PWA
- Paiement : NimbaPay (système national de paiement instantané guinéen, opéré par la
  Guinéenne de Monétique/BCRG) comme moyen principal, avec cash on delivery en filet
  de sécurité. La documentation API NimbaPay n'est pas encore intégrée à ce projet :
  le module de paiement doit donc être conçu de façon abstraite (interface
  PaymentProvider) pour pouvoir brancher l'implémentation NimbaPay dès que les
  spécifications techniques seront obtenues auprès de GuiM, sans refonte.
- Devise : Franc guinéen (GNF), montants en entiers, pas de décimales
- Langue interface : français
- Connectivité cible : réseaux mobiles lents, prévoir optimisation des assets

OBJECTIF DE CETTE PREMIÈRE ITÉRATION
Mettre en place le socle technique du backend :
1. Structure de projet FastAPI modulaire (voir arborescence du cahier des charges,
   section 5.2) avec Docker + docker-compose (API + PostgreSQL + Redis)
2. Configuration (variables d'environnement via pydantic-settings), gestion des
   secrets, connexion base de données asynchrone
3. Modèle de données initial (SQLAlchemy) pour : User, Vendor, Category, Product,
   avec migrations Alembic
4. Authentification : inscription/connexion par téléphone, hashing sécurisé du
   mot de passe, émission de JWT (access + refresh token), middleware de
   dépendance pour protéger les routes par rôle (acheteur / vendeur / admin)
5. Endpoints CRUD de base pour Category et Product (avec pagination et filtres
   simples : catégorie, prix min/max, disponibilité)
6. Tests unitaires de base (pytest) pour l'authentification et le CRUD produit
7. Fichier README expliquant comment lancer le projet en local

CONTRAINTES
- Code en anglais (noms de variables/fonctions), mais messages d'erreur API et
  réponses destinées à l'utilisateur en français
- Respecter une architecture propre (séparation router / service / repository)
- Documenter chaque module avec des docstrings concises
- Ne pas implémenter le paiement ni la livraison dans cette itération — se
  concentrer uniquement sur le socle décrit ci-dessus

Une fois ce socle posé, nous itérerons module par module en suivant le plan de
développement en 8 étapes du cahier des charges (section 8), en commençant par
la gestion complète des vendeurs et le panier multi-vendeurs.

Avant de commencer à écrire du code, propose-moi l'arborescence détaillée des
fichiers que tu vas créer, pour validation.
```

\---

## 10\. Prochaines étapes suggérées

* Valider ce cahier des charges (ajustements, priorités)
* **Contacter la Guinéenne de Monétique (GuiM) / BCRG** pour obtenir l'accès marchand NimbaPay et la documentation technique d'intégration (API, environnement de test, identifiants) — c'est le point bloquant principal pour l'intégration réelle du paiement
* Lancer Claude Code avec le prompt de la section 9 pour démarrer le socle technique (le module paiement sera posé en interface abstraite, prêt à recevoir NimbaPay)

