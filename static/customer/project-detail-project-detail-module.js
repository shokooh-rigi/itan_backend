(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["project-detail-project-detail-module"],{

/***/ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/project-detail/project-detail.component.html":
/*!**********************************************************************************************************!*\
  !*** ./node_modules/raw-loader/dist/cjs.js!./src/app/pages/project-detail/project-detail.component.html ***!
  \**********************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("<mat-card class=\"app-project-card\">\n    <div class=\"mat-card-header\">\n        <div class=\"mat-card-title\">{{details.title}}</div>\n    </div>\n\n    <mat-card-content>\n        <div class=\"app-address\">\n            <p class=\"app-part-1\">{{details.address.part1}}</p>\n            <p class=\"app-part-2\">{{details.address.part2}}</p>\n        </div>\n        <div class=\"app-info\">\n            <p class=\"app-part-1\">Estimator: <span>{{details.estimator}}</span></p>\n            <p class=\"app-part-2\">Tech: <span>{{details.tech}}</span></p>\n        </div>\n        <div class=\"app-progress\">\n            <app-step-progress-bar [steps]=\"steps\" [properties]=\"properties\"></app-step-progress-bar>\n        </div>\n    </mat-card-content>\n</mat-card>");

/***/ }),

/***/ "./src/app/pages/project-detail/project-detail-routing.module.ts":
/*!***********************************************************************!*\
  !*** ./src/app/pages/project-detail/project-detail-routing.module.ts ***!
  \***********************************************************************/
/*! exports provided: ProjectDetailRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectDetailRoutingModule", function() { return ProjectDetailRoutingModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm2015/router.js");
/* harmony import */ var _project_detail_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./project-detail.component */ "./src/app/pages/project-detail/project-detail.component.ts");




const routes = [{ path: '', component: _project_detail_component__WEBPACK_IMPORTED_MODULE_3__["ProjectDetailComponent"] }];
let ProjectDetailRoutingModule = class ProjectDetailRoutingModule {
};
ProjectDetailRoutingModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        imports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"].forChild(routes)],
        exports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"]]
    })
], ProjectDetailRoutingModule);



/***/ }),

/***/ "./src/app/pages/project-detail/project-detail.component.scss":
/*!********************************************************************!*\
  !*** ./src/app/pages/project-detail/project-detail.component.scss ***!
  \********************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3BhZ2VzL3Byb2plY3QtZGV0YWlsL3Byb2plY3QtZGV0YWlsLmNvbXBvbmVudC5zY3NzIn0= */");

/***/ }),

/***/ "./src/app/pages/project-detail/project-detail.component.ts":
/*!******************************************************************!*\
  !*** ./src/app/pages/project-detail/project-detail.component.ts ***!
  \******************************************************************/
/*! exports provided: ProjectDetailComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectDetailComponent", function() { return ProjectDetailComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


let ProjectDetailComponent = class ProjectDetailComponent {
    constructor() { }
    ngOnInit() {
    }
};
ProjectDetailComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-project-detail',
        template: tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! raw-loader!./project-detail.component.html */ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/project-detail/project-detail.component.html")).default,
        styles: [tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! ./project-detail.component.scss */ "./src/app/pages/project-detail/project-detail.component.scss")).default]
    })
], ProjectDetailComponent);



/***/ }),

/***/ "./src/app/pages/project-detail/project-detail.module.ts":
/*!***************************************************************!*\
  !*** ./src/app/pages/project-detail/project-detail.module.ts ***!
  \***************************************************************/
/*! exports provided: RequestProjectDetailModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestProjectDetailModule", function() { return RequestProjectDetailModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _project_detail_routing_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./project-detail-routing.module */ "./src/app/pages/project-detail/project-detail-routing.module.ts");
/* harmony import */ var _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../shared/shared.module */ "./src/app/shared/shared.module.ts");
/* harmony import */ var _project_detail_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./project-detail.component */ "./src/app/pages/project-detail/project-detail.component.ts");





let RequestProjectDetailModule = class RequestProjectDetailModule {
};
RequestProjectDetailModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        declarations: [
            _project_detail_component__WEBPACK_IMPORTED_MODULE_4__["ProjectDetailComponent"]
        ],
        imports: [
            _project_detail_routing_module__WEBPACK_IMPORTED_MODULE_2__["ProjectDetailRoutingModule"],
            _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__["SharedModule"]
        ]
    })
], RequestProjectDetailModule);



/***/ })

}]);
//# sourceMappingURL=project-detail-project-detail-module.js.map