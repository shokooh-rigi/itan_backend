(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["projects-projects-module"],{

/***/ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/project/project.component.html":
/*!*****************************************************************************************************!*\
  !*** ./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/project/project.component.html ***!
  \*****************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("<mat-card class=\"app-project-card\">\r\n    <div class=\"mat-card-header\">\r\n        <div class=\"mat-card-title\">{{details.title}}</div>\r\n    </div>\r\n\r\n    <mat-card-content>\r\n        <div class=\"app-address\">\r\n            <p class=\"app-part-1\">{{details.address.part1}}</p>\r\n            <p class=\"app-part-2\">{{details.address.part2}}</p>\r\n        </div>\r\n        <div class=\"app-info\">\r\n            <p class=\"app-part-1\">Estimator: <span>{{details.estimator}}</span></p>\r\n            <p class=\"app-part-2\">Tech: <span>{{details.tech}}</span></p>\r\n        </div>\r\n        <div class=\"app-progress\">\r\n            <app-step-progress-bar [steps]=\"steps\" [properties]=\"properties\"></app-step-progress-bar>\r\n        </div>\r\n    </mat-card-content>\r\n</mat-card>");

/***/ }),

/***/ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/projects-filter/projects-filter.component.html":
/*!*********************************************************************************************************************!*\
  !*** ./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/projects-filter/projects-filter.component.html ***!
  \*********************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("<div class=\"app-filter\">\r\n    <form (ngSubmit)=\"submitDateFilter()\" ngNativeValidate class=\"app-date-filter-form\">\r\n        <div class=\"row\">\r\n            <div class=\"col-12\">\r\n                <h5>Filter By Creation Date</h5>\r\n            </div>\r\n        </div>\r\n\r\n        <div class=\"row\">\r\n            <div class=\"col-12\">\r\n                <label for=\"fromDate\" class=\"control-label\">Creation Date From:</label>\r\n                <input type=\"text\" [(ngModel)]=\"fromDate\" name=\"fromDate\" placeholder=\"mm/dd/YYYY\"\r\n                    pattern=\"\\d{2}[\\/]\\d{2}[\\/]\\d{4}\" class=\"form-control\" required id=\"fromDate\" />\r\n            </div>\r\n        </div>\r\n\r\n        <div class=\"row\">\r\n            <div class=\"col-12\">\r\n                <label for=\"toDate\" class=\"control-label\">Creation Date To:</label>\r\n                <input type=\"text\" [(ngModel)]=\"toDate\" name=\"toDate\" placeholder=\"mm/dd/YYYY\"\r\n                    pattern=\"\\d{2}[\\/]\\d{2}[\\/]\\d{4}\" class=\"form-control\" required id=\"toDate\" />\r\n            </div>\r\n        </div>\r\n\r\n        <div class=\"row\">\r\n            <div class=\"col-12\">\r\n                <button mat-raised-button color=\"b-success\" type=\"submit\">Submit</button>\r\n                <button mat-raised-button color=\"b-primary\" type=\"button\" (click)=\"clearDateFilter()\">clear\r\n                    filter</button>\r\n            </div>\r\n        </div>\r\n\r\n        <div class=\"row\">\r\n            <div class=\"offset-lg-2 col-12 col-lg-8\">\r\n                <ngb-alert *ngIf=\"dateError\" type=\"danger\" [innerHTML]=\"dateError\" [dismissible]=\"false\"></ngb-alert>\r\n                <ngb-alert *ngIf=\"dateMessage\" type=\"secondary\" [innerHTML]=\"dateMessage\" [dismissible]=\"false\">\r\n                </ngb-alert>\r\n            </div>\r\n        </div>\r\n    </form>\r\n\r\n    <div class=\"row app-search-and-pagination\">\r\n        <div class=\"col-12 col-lg-4 app-search-box\">\r\n            <input type=\"text\" class=\"form-control\" placeholder=\"Project...\" [(ngModel)]=\"search\" />\r\n            <button mat-raised-button color=\"b-primary\" (click)=\"onSearchChange()\">\r\n                <mat-icon>search</mat-icon>\r\n            </button>\r\n        </div>\r\n        <div class=\"col-12 col-lg-4 app-pages-count-box\">\r\n            Number of rows: {{itemsCount}}\r\n        </div>\r\n        <div class=\"col-12 col-lg-4 app-page-size-box\">\r\n            <label class=\"app-title\">Items Per Page</label>\r\n            <div class=\"btn-group btn-group-toggle\" ngbRadioGroup name=\"pageSizeRadioGroup\" [(ngModel)]=\"pageSize\"\r\n                (change)=\"onPageSizeChange()\">\r\n                <label ngbButtonLabel class=\"btn-outline-primary\">\r\n                    <input ngbButton type=\"radio\" [value]=\"5\"> 5\r\n                </label>\r\n                <label ngbButtonLabel class=\"btn-outline-primary\">\r\n                    <input ngbButton type=\"radio\" [value]=\"20\"> 20\r\n                </label>\r\n                <label ngbButtonLabel class=\"btn-outline-primary\">\r\n                    <input ngbButton type=\"radio\" [value]=\"50\"> 50\r\n                </label>\r\n                <label ngbButtonLabel class=\"btn-outline-primary\">\r\n                    <input ngbButton type=\"radio\" value=\"all\"> ALL\r\n                </label>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</div>");

/***/ }),

/***/ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/projects.component.html":
/*!**********************************************************************************************!*\
  !*** ./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/projects.component.html ***!
  \**********************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("<ng-template #viewModeBox>\r\n    <div class=\"col-12 app-view-mode-box\">\r\n        <label class=\"app-title\">View</label>\r\n        <div class=\"btn-group btn-group-toggle\" ngbRadioGroup name=\"pageSizeRadioGroup\" [ngModel]=\"viewMode\"\r\n            (ngModelChange)=\"changeViewMode($event)\">\r\n            <label ngbButtonLabel class=\"btn-outline-primary app-view-button\" placement=\"bottom\"\r\n                ngbTooltip=\"Grid&nbsp;View\">\r\n                <input ngbButton type=\"radio\" value=\"grid\">\r\n                <mat-icon>view_module</mat-icon>\r\n            </label>\r\n            <label ngbButtonLabel class=\"btn-outline-primary app-view-button\" placement=\"bottom\"\r\n                ngbTooltip=\"List&nbsp;View\">\r\n                <input ngbButton type=\"radio\" value=\"list\">\r\n                <mat-icon>list</mat-icon>\r\n            </label>\r\n        </div>\r\n    </div>\r\n</ng-template>\r\n\r\n\r\n<div *ngIf=\"isListView; else gridView\" class=\"container global-app-light-container app-list-view\">\r\n    <ng-container *ngTemplateOutlet=\"viewModeBox\"></ng-container>\r\n    <hr>\r\n\r\n    <ngb-alert *ngIf=\"resultMessage\" [type]=\"resultMessage.type\" [dismissible]=\"true\" (close)=\"closeMessage()\">\r\n        <div class=\"app-result-message\">\r\n            <div class=\"app-header\" [innerHTML]=\"resultMessage.header\"></div>\r\n            <div class=\"app-body\" [innerHTML]=\"resultMessage.body\"></div>\r\n        </div>\r\n    </ngb-alert>\r\n\r\n    <app-projects-filter [dateMessage]=\"dateFilterMessage\" [itemsCount]=\"projectsPageResult?.count\"\r\n        [fromDate]=\"filter.fromDate\" [toDate]=\"filter.toDate\" [search]=\"filter.search\" [pageSize]=\"filter.page_size\"\r\n        (dateChange)=\"onDateChange($event)\" (searchChange)=\"onSearchChange($event)\"\r\n        (pageSizeChange)=\"onPageSizeChange($event)\">\r\n    </app-projects-filter>\r\n\r\n    <div class=\"app-list-view-projects\">\r\n        <table class=\"table table-striped app-projects-table\">\r\n            <thead>\r\n                <tr>\r\n                    <th scope=\"col\" class=\"app-sortable-th\">\r\n                        <button mat-button color=\"b-primary\" (click)=\"onOrderingChange(Ordering.project)\">\r\n                            Project\r\n                            <i *ngIf=\"filter.ordering === Ordering.project\" class=\"material-icons app-arrow\">\r\n                                {{filter.asc ? 'arrow_drop_up' : 'arrow_drop_down'}}\r\n                            </i>\r\n                        </button>\r\n                    </th>\r\n                    <th scope=\"col\">Address</th>\r\n                    <th scope=\"col\">City</th>\r\n                    <th scope=\"col\">State</th>\r\n                    <th scope=\"col\">Zip</th>\r\n                    <th scope=\"col\">Estimator</th>\r\n                    <th scope=\"col\">Tech</th>\r\n                    <th scope=\"col\" class=\"app-sortable-th\">\r\n                        <button mat-button color=\"b-primary\" (click)=\"onOrderingChange(Ordering.creationDate)\">\r\n                            Creation Date\r\n                            <i *ngIf=\"filter.ordering === Ordering.creationDate\" class=\"material-icons app-arrow\">\r\n                                {{filter.asc ? 'arrow_drop_up' : 'arrow_drop_down'}}\r\n                            </i>\r\n                        </button>\r\n                    </th>\r\n                </tr>\r\n            </thead>\r\n            <tbody>\r\n                <tr *ngFor=\"let project of projects\">\r\n                    <td>{{project.name}}</td>\r\n                    <td>{{project.address_line_1}}</td>\r\n                    <td>{{project.city}}</td>\r\n                    <td>{{project.state}}</td>\r\n                    <td>{{project.zip}}</td>\r\n                    <td>{{project.estimator}}</td>\r\n                    <td>{{project.tech}}</td>\r\n                    <td>{{project.created_on | date}}</td>\r\n                </tr>\r\n            </tbody>\r\n        </table>\r\n\r\n        <ngb-pagination *ngIf=\"projectsPageResult\" [collectionSize]=\"projectsPageResult.count\" [maxSize]=\"5\"\r\n            [rotate]=\"true\" [ellipses]=\"false\" [page]=\"filter.page\" [pageSize]=\"filter.page_size\" [boundaryLinks]=\"true\"\r\n            (pageChange)=\"onPageChange($event)\" class=\"d-flex justify-content-center\">\r\n        </ngb-pagination>\r\n    </div>\r\n</div>\r\n\r\n<ng-template #gridView>\r\n    <div class=\"container-fluid app-grid-view\">\r\n        <div class=\"global-app-light-container\">\r\n            <ng-container *ngTemplateOutlet=\"viewModeBox\"></ng-container>\r\n        </div>\r\n\r\n        <div class=\"app-projects\">\r\n            <div *ngFor=\"let project of projectsDetails\" class=\"app-project\">\r\n                <app-project [details]=\"project\"></app-project>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</ng-template>");

/***/ }),

/***/ "./src/app/pages/projects/project/project.component.scss":
/*!***************************************************************!*\
  !*** ./src/app/pages/projects/project/project.component.scss ***!
  \***************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = (".app-project-card {\n  width: 500px;\n  padding: 25px 25px 18px 25px;\n  background-color: #f0f0f0;\n  border: 1px solid #dddddd;\n  border-bottom: 4px solid black;\n  box-shadow: 35px 35px 50px rgba(0, 0, 0, 0.3);\n}\n.app-project-card .mat-card-header .mat-card-title {\n  text-transform: uppercase;\n  font-weight: bold;\n  font-size: 18px;\n  white-space: nowrap;\n  text-overflow: ellipsis;\n  overflow: hidden;\n  margin-bottom: 2px;\n}\n.app-project-card mat-card-content .app-address .app-part-1 {\n  margin-bottom: 3px;\n}\n.app-project-card mat-card-content .app-address .app-part-2 {\n  margin-top: 0;\n}\n.app-project-card mat-card-content .app-info .app-part-1 {\n  margin-bottom: 3px;\n}\n.app-project-card mat-card-content .app-info .app-part-2 {\n  margin-top: 0;\n  margin-bottom: 22px;\n}\n.app-project-card mat-card-content .app-progress {\n  width: calc(100% + 50px);\n  position: relative;\n  left: -25px;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvcGFnZXMvcHJvamVjdHMvcHJvamVjdC9DOlxccHl0aG9ucHJvamVjdHNcXDE1XFxjdXN0b21lci1kYXNoYm9hcmQvc3JjXFxhcHBcXHBhZ2VzXFxwcm9qZWN0c1xccHJvamVjdFxccHJvamVjdC5jb21wb25lbnQuc2NzcyIsInNyYy9hcHAvcGFnZXMvcHJvamVjdHMvcHJvamVjdC9wcm9qZWN0LmNvbXBvbmVudC5zY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBO0VBQ0UsWUFBQTtFQUNBLDRCQUFBO0VBQ0EseUJBQUE7RUFDQSx5QkFBQTtFQUNBLDhCQUFBO0VBQ0EsNkNBQUE7QUNDRjtBREVJO0VBQ0UseUJBQUE7RUFDQSxpQkFBQTtFQUNBLGVBQUE7RUFDQSxtQkFBQTtFQUNBLHVCQUFBO0VBQ0EsZ0JBQUE7RUFDQSxrQkFBQTtBQ0FOO0FETU07RUFDRSxrQkFBQTtBQ0pSO0FET007RUFDRSxhQUFBO0FDTFI7QURVTTtFQUNFLGtCQUFBO0FDUlI7QURXTTtFQUNFLGFBQUE7RUFDQSxtQkFBQTtBQ1RSO0FEYUk7RUFDRSx3QkFBQTtFQUNBLGtCQUFBO0VBQ0EsV0FBQTtBQ1hOIiwiZmlsZSI6InNyYy9hcHAvcGFnZXMvcHJvamVjdHMvcHJvamVjdC9wcm9qZWN0LmNvbXBvbmVudC5zY3NzIiwic291cmNlc0NvbnRlbnQiOlsiLmFwcC1wcm9qZWN0LWNhcmQge1xyXG4gIHdpZHRoOiA1MDBweDtcclxuICBwYWRkaW5nOiAyNXB4IDI1cHggMThweCAyNXB4O1xyXG4gIGJhY2tncm91bmQtY29sb3I6ICNmMGYwZjA7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2RkZGRkZDtcclxuICBib3JkZXItYm90dG9tOiA0cHggc29saWQgYmxhY2s7XHJcbiAgYm94LXNoYWRvdzogMzVweCAzNXB4IDUwcHggcmdiYSgwLCAwLCAwLCAwLjMpO1xyXG5cclxuICAubWF0LWNhcmQtaGVhZGVyIHtcclxuICAgIC5tYXQtY2FyZC10aXRsZSB7XHJcbiAgICAgIHRleHQtdHJhbnNmb3JtOiB1cHBlcmNhc2U7XHJcbiAgICAgIGZvbnQtd2VpZ2h0OiBib2xkO1xyXG4gICAgICBmb250LXNpemU6IDE4cHg7XHJcbiAgICAgIHdoaXRlLXNwYWNlOiBub3dyYXA7XHJcbiAgICAgIHRleHQtb3ZlcmZsb3c6IGVsbGlwc2lzO1xyXG4gICAgICBvdmVyZmxvdzogaGlkZGVuO1xyXG4gICAgICBtYXJnaW4tYm90dG9tOiAycHg7XHJcbiAgICB9XHJcbiAgfVxyXG5cclxuICBtYXQtY2FyZC1jb250ZW50IHtcclxuICAgIC5hcHAtYWRkcmVzcyB7XHJcbiAgICAgIC5hcHAtcGFydC0xIHtcclxuICAgICAgICBtYXJnaW4tYm90dG9tOiAzcHg7XHJcbiAgICAgIH1cclxuXHJcbiAgICAgIC5hcHAtcGFydC0yIHtcclxuICAgICAgICBtYXJnaW4tdG9wOiAwO1xyXG4gICAgICB9XHJcbiAgICB9XHJcblxyXG4gICAgLmFwcC1pbmZvIHtcclxuICAgICAgLmFwcC1wYXJ0LTEge1xyXG4gICAgICAgIG1hcmdpbi1ib3R0b206IDNweDtcclxuICAgICAgfVxyXG5cclxuICAgICAgLmFwcC1wYXJ0LTIge1xyXG4gICAgICAgIG1hcmdpbi10b3A6IDA7XHJcbiAgICAgICAgbWFyZ2luLWJvdHRvbTogMjJweDtcclxuICAgICAgfVxyXG4gICAgfVxyXG5cclxuICAgIC5hcHAtcHJvZ3Jlc3Mge1xyXG4gICAgICB3aWR0aDogY2FsYygxMDAlICsgNTBweCk7XHJcbiAgICAgIHBvc2l0aW9uOiByZWxhdGl2ZTtcclxuICAgICAgbGVmdDogLTI1cHg7XHJcbiAgICB9XHJcbiAgfVxyXG59XHJcbiIsIi5hcHAtcHJvamVjdC1jYXJkIHtcbiAgd2lkdGg6IDUwMHB4O1xuICBwYWRkaW5nOiAyNXB4IDI1cHggMThweCAyNXB4O1xuICBiYWNrZ3JvdW5kLWNvbG9yOiAjZjBmMGYwO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZGRkZGRkO1xuICBib3JkZXItYm90dG9tOiA0cHggc29saWQgYmxhY2s7XG4gIGJveC1zaGFkb3c6IDM1cHggMzVweCA1MHB4IHJnYmEoMCwgMCwgMCwgMC4zKTtcbn1cbi5hcHAtcHJvamVjdC1jYXJkIC5tYXQtY2FyZC1oZWFkZXIgLm1hdC1jYXJkLXRpdGxlIHtcbiAgdGV4dC10cmFuc2Zvcm06IHVwcGVyY2FzZTtcbiAgZm9udC13ZWlnaHQ6IGJvbGQ7XG4gIGZvbnQtc2l6ZTogMThweDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7XG4gIG92ZXJmbG93OiBoaWRkZW47XG4gIG1hcmdpbi1ib3R0b206IDJweDtcbn1cbi5hcHAtcHJvamVjdC1jYXJkIG1hdC1jYXJkLWNvbnRlbnQgLmFwcC1hZGRyZXNzIC5hcHAtcGFydC0xIHtcbiAgbWFyZ2luLWJvdHRvbTogM3B4O1xufVxuLmFwcC1wcm9qZWN0LWNhcmQgbWF0LWNhcmQtY29udGVudCAuYXBwLWFkZHJlc3MgLmFwcC1wYXJ0LTIge1xuICBtYXJnaW4tdG9wOiAwO1xufVxuLmFwcC1wcm9qZWN0LWNhcmQgbWF0LWNhcmQtY29udGVudCAuYXBwLWluZm8gLmFwcC1wYXJ0LTEge1xuICBtYXJnaW4tYm90dG9tOiAzcHg7XG59XG4uYXBwLXByb2plY3QtY2FyZCBtYXQtY2FyZC1jb250ZW50IC5hcHAtaW5mbyAuYXBwLXBhcnQtMiB7XG4gIG1hcmdpbi10b3A6IDA7XG4gIG1hcmdpbi1ib3R0b206IDIycHg7XG59XG4uYXBwLXByb2plY3QtY2FyZCBtYXQtY2FyZC1jb250ZW50IC5hcHAtcHJvZ3Jlc3Mge1xuICB3aWR0aDogY2FsYygxMDAlICsgNTBweCk7XG4gIHBvc2l0aW9uOiByZWxhdGl2ZTtcbiAgbGVmdDogLTI1cHg7XG59Il19 */");

/***/ }),

/***/ "./src/app/pages/projects/project/project.component.ts":
/*!*************************************************************!*\
  !*** ./src/app/pages/projects/project/project.component.ts ***!
  \*************************************************************/
/*! exports provided: ProjectComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectComponent", function() { return ProjectComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


let ProjectComponent = class ProjectComponent {
    constructor() {
        this.properties = {
            iconSize: 30,
            connectorHeight: 10,
            fontSize: '12px',
            activeColor: '#019ada',
            inactiveColor: '#c1d9e5',
            activeTextColor: 'black',
            inactiveTextColor: '#787878'
        };
        this.steps = [
            { title: 'estimate', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
            { title: 'quote', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
            { title: 'proposal', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
            { title: 'order', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
            { title: 'invoice', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
            { title: 'report', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
            { title: 'payment', passed: false, active: false, icon: 'assets/images/shared/step-progress-bar/check.svg' },
        ];
    }
    set details(value) {
        this._details = value;
        for (const step of this.steps) {
            step.passed = false;
            step.active = false;
        }
        for (let i = 0; i < value.passedSteps && i < this.steps.length; i++) {
            this.steps[i].passed = true;
        }
        if (0 < value.passedSteps && value.passedSteps <= this.steps.length) {
            this.steps[value.passedSteps - 1].active = true;
        }
    }
    ;
    get details() {
        return this._details;
    }
    ngOnInit() {
    }
};
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectComponent.prototype, "details", null);
ProjectComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-project',
        template: tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! raw-loader!./project.component.html */ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/project/project.component.html")).default,
        styles: [tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! ./project.component.scss */ "./src/app/pages/projects/project/project.component.scss")).default]
    })
], ProjectComponent);



/***/ }),

/***/ "./src/app/pages/projects/projects-filter/projects-filter.component.scss":
/*!*******************************************************************************!*\
  !*** ./src/app/pages/projects/projects-filter/projects-filter.component.scss ***!
  \*******************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = (".app-filter .app-date-filter-form {\n  text-align: center;\n}\n.app-filter .app-date-filter-form .row {\n  margin-bottom: 15px;\n}\n.app-filter .app-date-filter-form .row label {\n  display: inline-block;\n  width: 200px;\n  padding: 5px;\n  text-align: left;\n}\n.app-filter .app-date-filter-form .row input {\n  display: inline-block;\n  width: 250px;\n}\n.app-filter .app-date-filter-form .row button {\n  text-transform: uppercase;\n  margin: 5px 10px auto auto;\n}\n.app-filter .app-search-and-pagination {\n  margin: 30px 0 20px;\n}\n.app-filter .app-search-and-pagination .app-search-box {\n  padding-left: 0;\n}\n.app-filter .app-search-and-pagination .app-search-box input {\n  display: inline-block;\n  vertical-align: top;\n  width: 250px;\n  margin-right: 10px;\n}\n.app-filter .app-search-and-pagination .app-search-box button {\n  display: inline-block;\n  vertical-align: top;\n}\n.app-filter .app-search-and-pagination .app-pages-count-box {\n  text-align: center;\n  line-height: calc(1.5em + 0.75rem + 2px);\n}\n.app-filter .app-search-and-pagination .app-page-size-box {\n  text-align: right;\n}\n.app-filter .app-search-and-pagination .app-page-size-box .app-title {\n  margin-right: 10px;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvcGFnZXMvcHJvamVjdHMvcHJvamVjdHMtZmlsdGVyL0M6XFxweXRob25wcm9qZWN0c1xcMTVcXGN1c3RvbWVyLWRhc2hib2FyZC9zcmNcXGFwcFxccGFnZXNcXHByb2plY3RzXFxwcm9qZWN0cy1maWx0ZXJcXHByb2plY3RzLWZpbHRlci5jb21wb25lbnQuc2NzcyIsInNyYy9hcHAvcGFnZXMvcHJvamVjdHMvcHJvamVjdHMtZmlsdGVyL3Byb2plY3RzLWZpbHRlci5jb21wb25lbnQuc2NzcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFDRTtFQUNFLGtCQUFBO0FDQUo7QURFSTtFQUNFLG1CQUFBO0FDQU47QURFTTtFQUNFLHFCQUFBO0VBQ0EsWUFBQTtFQUNBLFlBQUE7RUFDQSxnQkFBQTtBQ0FSO0FER007RUFDRSxxQkFBQTtFQUNBLFlBQUE7QUNEUjtBRElNO0VBQ0UseUJBQUE7RUFDQSwwQkFBQTtBQ0ZSO0FET0U7RUFDRSxtQkFBQTtBQ0xKO0FET0k7RUFDRSxlQUFBO0FDTE47QURPTTtFQUNFLHFCQUFBO0VBQ0EsbUJBQUE7RUFDQSxZQUFBO0VBQ0Esa0JBQUE7QUNMUjtBRFFNO0VBQ0UscUJBQUE7RUFDQSxtQkFBQTtBQ05SO0FEVUk7RUFDRSxrQkFBQTtFQUNBLHdDQUFBO0FDUk47QURXSTtFQUNFLGlCQUFBO0FDVE47QURXTTtFQUNFLGtCQUFBO0FDVFIiLCJmaWxlIjoic3JjL2FwcC9wYWdlcy9wcm9qZWN0cy9wcm9qZWN0cy1maWx0ZXIvcHJvamVjdHMtZmlsdGVyLmNvbXBvbmVudC5zY3NzIiwic291cmNlc0NvbnRlbnQiOlsiLmFwcC1maWx0ZXIge1xyXG4gIC5hcHAtZGF0ZS1maWx0ZXItZm9ybSB7XHJcbiAgICB0ZXh0LWFsaWduOiBjZW50ZXI7XHJcblxyXG4gICAgLnJvdyB7XHJcbiAgICAgIG1hcmdpbi1ib3R0b206IDE1cHg7XHJcblxyXG4gICAgICBsYWJlbCB7XHJcbiAgICAgICAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xyXG4gICAgICAgIHdpZHRoOiAyMDBweDtcclxuICAgICAgICBwYWRkaW5nOiA1cHg7XHJcbiAgICAgICAgdGV4dC1hbGlnbjogbGVmdDtcclxuICAgICAgfVxyXG5cclxuICAgICAgaW5wdXQge1xyXG4gICAgICAgIGRpc3BsYXk6IGlubGluZS1ibG9jaztcclxuICAgICAgICB3aWR0aDogMjUwcHg7XHJcbiAgICAgIH1cclxuXHJcbiAgICAgIGJ1dHRvbiB7XHJcbiAgICAgICAgdGV4dC10cmFuc2Zvcm06IHVwcGVyY2FzZTtcclxuICAgICAgICBtYXJnaW46IDVweCAxMHB4IGF1dG8gYXV0bztcclxuICAgICAgfVxyXG4gICAgfVxyXG4gIH1cclxuXHJcbiAgLmFwcC1zZWFyY2gtYW5kLXBhZ2luYXRpb24ge1xyXG4gICAgbWFyZ2luOiAzMHB4IDAgMjBweDtcclxuXHJcbiAgICAuYXBwLXNlYXJjaC1ib3gge1xyXG4gICAgICBwYWRkaW5nLWxlZnQ6IDA7XHJcblxyXG4gICAgICBpbnB1dCB7XHJcbiAgICAgICAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xyXG4gICAgICAgIHZlcnRpY2FsLWFsaWduOiB0b3A7XHJcbiAgICAgICAgd2lkdGg6IDI1MHB4O1xyXG4gICAgICAgIG1hcmdpbi1yaWdodDogMTBweDtcclxuICAgICAgfVxyXG5cclxuICAgICAgYnV0dG9uIHtcclxuICAgICAgICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XHJcbiAgICAgICAgdmVydGljYWwtYWxpZ246IHRvcDtcclxuICAgICAgfVxyXG4gICAgfVxyXG5cclxuICAgIC5hcHAtcGFnZXMtY291bnQtYm94IHtcclxuICAgICAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gICAgICBsaW5lLWhlaWdodDogY2FsYygxLjVlbSArIDAuNzVyZW0gKyAycHgpO1xyXG4gICAgfVxyXG5cclxuICAgIC5hcHAtcGFnZS1zaXplLWJveCB7XHJcbiAgICAgIHRleHQtYWxpZ246IHJpZ2h0O1xyXG5cclxuICAgICAgLmFwcC10aXRsZSB7XHJcbiAgICAgICAgbWFyZ2luLXJpZ2h0OiAxMHB4O1xyXG4gICAgICB9XHJcbiAgICB9XHJcbiAgfVxyXG59XHJcbiIsIi5hcHAtZmlsdGVyIC5hcHAtZGF0ZS1maWx0ZXItZm9ybSB7XG4gIHRleHQtYWxpZ246IGNlbnRlcjtcbn1cbi5hcHAtZmlsdGVyIC5hcHAtZGF0ZS1maWx0ZXItZm9ybSAucm93IHtcbiAgbWFyZ2luLWJvdHRvbTogMTVweDtcbn1cbi5hcHAtZmlsdGVyIC5hcHAtZGF0ZS1maWx0ZXItZm9ybSAucm93IGxhYmVsIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xuICB3aWR0aDogMjAwcHg7XG4gIHBhZGRpbmc6IDVweDtcbiAgdGV4dC1hbGlnbjogbGVmdDtcbn1cbi5hcHAtZmlsdGVyIC5hcHAtZGF0ZS1maWx0ZXItZm9ybSAucm93IGlucHV0IHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xuICB3aWR0aDogMjUwcHg7XG59XG4uYXBwLWZpbHRlciAuYXBwLWRhdGUtZmlsdGVyLWZvcm0gLnJvdyBidXR0b24ge1xuICB0ZXh0LXRyYW5zZm9ybTogdXBwZXJjYXNlO1xuICBtYXJnaW46IDVweCAxMHB4IGF1dG8gYXV0bztcbn1cbi5hcHAtZmlsdGVyIC5hcHAtc2VhcmNoLWFuZC1wYWdpbmF0aW9uIHtcbiAgbWFyZ2luOiAzMHB4IDAgMjBweDtcbn1cbi5hcHAtZmlsdGVyIC5hcHAtc2VhcmNoLWFuZC1wYWdpbmF0aW9uIC5hcHAtc2VhcmNoLWJveCB7XG4gIHBhZGRpbmctbGVmdDogMDtcbn1cbi5hcHAtZmlsdGVyIC5hcHAtc2VhcmNoLWFuZC1wYWdpbmF0aW9uIC5hcHAtc2VhcmNoLWJveCBpbnB1dCB7XG4gIGRpc3BsYXk6IGlubGluZS1ibG9jaztcbiAgdmVydGljYWwtYWxpZ246IHRvcDtcbiAgd2lkdGg6IDI1MHB4O1xuICBtYXJnaW4tcmlnaHQ6IDEwcHg7XG59XG4uYXBwLWZpbHRlciAuYXBwLXNlYXJjaC1hbmQtcGFnaW5hdGlvbiAuYXBwLXNlYXJjaC1ib3ggYnV0dG9uIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xuICB2ZXJ0aWNhbC1hbGlnbjogdG9wO1xufVxuLmFwcC1maWx0ZXIgLmFwcC1zZWFyY2gtYW5kLXBhZ2luYXRpb24gLmFwcC1wYWdlcy1jb3VudC1ib3gge1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIGxpbmUtaGVpZ2h0OiBjYWxjKDEuNWVtICsgMC43NXJlbSArIDJweCk7XG59XG4uYXBwLWZpbHRlciAuYXBwLXNlYXJjaC1hbmQtcGFnaW5hdGlvbiAuYXBwLXBhZ2Utc2l6ZS1ib3gge1xuICB0ZXh0LWFsaWduOiByaWdodDtcbn1cbi5hcHAtZmlsdGVyIC5hcHAtc2VhcmNoLWFuZC1wYWdpbmF0aW9uIC5hcHAtcGFnZS1zaXplLWJveCAuYXBwLXRpdGxlIHtcbiAgbWFyZ2luLXJpZ2h0OiAxMHB4O1xufSJdfQ== */");

/***/ }),

/***/ "./src/app/pages/projects/projects-filter/projects-filter.component.ts":
/*!*****************************************************************************!*\
  !*** ./src/app/pages/projects/projects-filter/projects-filter.component.ts ***!
  \*****************************************************************************/
/*! exports provided: ProjectsFilterComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectsFilterComponent", function() { return ProjectsFilterComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


let ProjectsFilterComponent = class ProjectsFilterComponent {
    constructor() {
        this.fromDate = '';
        this.toDate = '';
        this.search = '';
        this.pageSize = 20;
        this.dateChange = new _angular_core__WEBPACK_IMPORTED_MODULE_1__["EventEmitter"]();
        this.searchChange = new _angular_core__WEBPACK_IMPORTED_MODULE_1__["EventEmitter"]();
        this.pageSizeChange = new _angular_core__WEBPACK_IMPORTED_MODULE_1__["EventEmitter"]();
    }
    ngOnInit() {
    }
    submitDateFilter() {
        clearTimeout(this.dateErrorTimeout);
        this.dateError = null;
        // Check date validation
        const fromDate = new Date(this.fromDate);
        const toDate = new Date(this.toDate);
        if (fromDate.getTime() > toDate.getTime()) {
            this.dateError = '<strong>Error!</strong> To Date must be greater or equal to Form Date.';
            this.dateErrorTimeout = setTimeout(() => this.dateError = null, 5000);
            return;
        }
        // Send entered dates to parent component
        this.dateChange.emit({ from: this.fromDate, to: this.toDate });
    }
    clearDateFilter() {
        this.dateError = null;
        this.fromDate = '';
        this.toDate = '';
        // Send empty dates to parent component
        this.dateChange.emit({ from: this.fromDate, to: this.toDate });
    }
    onSearchChange() {
        this.search = this.search.trim();
        this.searchChange.emit(this.search);
    }
    onPageSizeChange() {
        this.pageSizeChange.emit(this.pageSize);
    }
};
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectsFilterComponent.prototype, "dateMessage", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectsFilterComponent.prototype, "itemsCount", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectsFilterComponent.prototype, "fromDate", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectsFilterComponent.prototype, "toDate", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectsFilterComponent.prototype, "search", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Input"])()
], ProjectsFilterComponent.prototype, "pageSize", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Output"])()
], ProjectsFilterComponent.prototype, "dateChange", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Output"])()
], ProjectsFilterComponent.prototype, "searchChange", void 0);
tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Output"])()
], ProjectsFilterComponent.prototype, "pageSizeChange", void 0);
ProjectsFilterComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-projects-filter',
        template: tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! raw-loader!./projects-filter.component.html */ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/projects-filter/projects-filter.component.html")).default,
        styles: [tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! ./projects-filter.component.scss */ "./src/app/pages/projects/projects-filter/projects-filter.component.scss")).default]
    })
], ProjectsFilterComponent);



/***/ }),

/***/ "./src/app/pages/projects/projects-routing.module.ts":
/*!***********************************************************!*\
  !*** ./src/app/pages/projects/projects-routing.module.ts ***!
  \***********************************************************/
/*! exports provided: ProjectsRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectsRoutingModule", function() { return ProjectsRoutingModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm2015/router.js");
/* harmony import */ var _projects_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./projects.component */ "./src/app/pages/projects/projects.component.ts");




const routes = [{ path: '', component: _projects_component__WEBPACK_IMPORTED_MODULE_3__["ProjectsComponent"] }];
let ProjectsRoutingModule = class ProjectsRoutingModule {
};
ProjectsRoutingModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        imports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"].forChild(routes)],
        exports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"]]
    })
], ProjectsRoutingModule);



/***/ }),

/***/ "./src/app/pages/projects/projects.component.scss":
/*!********************************************************!*\
  !*** ./src/app/pages/projects/projects.component.scss ***!
  \********************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = (".app-view-mode-box {\n  text-align: end;\n}\n.app-view-mode-box .app-title {\n  margin-right: 10px;\n}\n.app-view-mode-box .app-view-button {\n  padding: 0;\n  width: 38px;\n  height: 38px;\n}\n.app-view-mode-box .app-view-button mat-icon {\n  font-size: 36px;\n  width: 36px;\n  height: 36px;\n}\n.app-result-message .app-header {\n  text-align: center;\n  font-size: 16px;\n  margin-bottom: 5px;\n}\n.app-result-message .app-body {\n  font-size: 16px;\n}\n.app-list-view {\n  margin: 0 auto;\n}\n.app-list-view .app-list-view-projects {\n  margin-top: 30px;\n}\n.app-list-view .app-list-view-projects .app-projects-table {\n  border-collapse: collapse;\n}\n.app-list-view .app-list-view-projects .app-projects-table .app-sortable-th button {\n  font-weight: bold;\n  font-size: 16px;\n}\n.app-list-view .app-list-view-projects .app-projects-table .app-sortable-th i {\n  vertical-align: middle;\n}\n.app-grid-view {\n  margin: 0 auto;\n}\n.app-grid-view .app-projects {\n  text-align: center;\n}\n.app-grid-view .app-projects .app-project {\n  text-align: start;\n  display: inline-block;\n  padding: 10px 25px 40px;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvcGFnZXMvcHJvamVjdHMvQzpcXHB5dGhvbnByb2plY3RzXFwxNVxcY3VzdG9tZXItZGFzaGJvYXJkL3NyY1xcYXBwXFxwYWdlc1xccHJvamVjdHNcXHByb2plY3RzLmNvbXBvbmVudC5zY3NzIiwic3JjL2FwcC9wYWdlcy9wcm9qZWN0cy9wcm9qZWN0cy5jb21wb25lbnQuc2NzcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTtFQUNFLGVBQUE7QUNDRjtBRENFO0VBQ0Usa0JBQUE7QUNDSjtBREVFO0VBQ0UsVUFBQTtFQUNBLFdBQUE7RUFDQSxZQUFBO0FDQUo7QURFSTtFQUNFLGVBQUE7RUFDQSxXQUFBO0VBQ0EsWUFBQTtBQ0FOO0FETUU7RUFDRSxrQkFBQTtFQUNBLGVBQUE7RUFDQSxrQkFBQTtBQ0hKO0FETUU7RUFDRSxlQUFBO0FDSko7QURRQTtFQUNFLGNBQUE7QUNMRjtBRE9FO0VBQ0UsZ0JBQUE7QUNMSjtBRE9JO0VBQ0UseUJBQUE7QUNMTjtBRFFRO0VBQ0UsaUJBQUE7RUFDQSxlQUFBO0FDTlY7QURTUTtFQUNFLHNCQUFBO0FDUFY7QURjQTtFQUNFLGNBQUE7QUNYRjtBRGFFO0VBQ0Usa0JBQUE7QUNYSjtBRGFJO0VBQ0UsaUJBQUE7RUFDQSxxQkFBQTtFQUNBLHVCQUFBO0FDWE4iLCJmaWxlIjoic3JjL2FwcC9wYWdlcy9wcm9qZWN0cy9wcm9qZWN0cy5jb21wb25lbnQuc2NzcyIsInNvdXJjZXNDb250ZW50IjpbIi5hcHAtdmlldy1tb2RlLWJveCB7XHJcbiAgdGV4dC1hbGlnbjogZW5kO1xyXG5cclxuICAuYXBwLXRpdGxlIHtcclxuICAgIG1hcmdpbi1yaWdodDogMTBweDtcclxuICB9XHJcblxyXG4gIC5hcHAtdmlldy1idXR0b24ge1xyXG4gICAgcGFkZGluZzogMDtcclxuICAgIHdpZHRoOiAzOHB4O1xyXG4gICAgaGVpZ2h0OiAzOHB4O1xyXG5cclxuICAgIG1hdC1pY29uIHtcclxuICAgICAgZm9udC1zaXplOiAzNnB4O1xyXG4gICAgICB3aWR0aDogMzZweDtcclxuICAgICAgaGVpZ2h0OiAzNnB4O1xyXG4gICAgfVxyXG4gIH1cclxufVxyXG5cclxuLmFwcC1yZXN1bHQtbWVzc2FnZSB7XHJcbiAgLmFwcC1oZWFkZXIge1xyXG4gICAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gICAgZm9udC1zaXplOiAxNnB4O1xyXG4gICAgbWFyZ2luLWJvdHRvbTogNXB4O1xyXG4gIH1cclxuXHJcbiAgLmFwcC1ib2R5IHtcclxuICAgIGZvbnQtc2l6ZTogMTZweDtcclxuICB9XHJcbn1cclxuXHJcbi5hcHAtbGlzdC12aWV3IHtcclxuICBtYXJnaW46IDAgYXV0bztcclxuXHJcbiAgLmFwcC1saXN0LXZpZXctcHJvamVjdHMge1xyXG4gICAgbWFyZ2luLXRvcDogMzBweDtcclxuXHJcbiAgICAuYXBwLXByb2plY3RzLXRhYmxlIHtcclxuICAgICAgYm9yZGVyLWNvbGxhcHNlOiBjb2xsYXBzZTtcclxuXHJcbiAgICAgIC5hcHAtc29ydGFibGUtdGgge1xyXG4gICAgICAgIGJ1dHRvbiB7XHJcbiAgICAgICAgICBmb250LXdlaWdodDogYm9sZDtcclxuICAgICAgICAgIGZvbnQtc2l6ZTogMTZweDtcclxuICAgICAgICB9XHJcblxyXG4gICAgICAgIGkge1xyXG4gICAgICAgICAgdmVydGljYWwtYWxpZ246IG1pZGRsZTtcclxuICAgICAgICB9XHJcbiAgICAgIH1cclxuICAgIH1cclxuICB9XHJcbn1cclxuXHJcbi5hcHAtZ3JpZC12aWV3IHtcclxuICBtYXJnaW46IDAgYXV0bztcclxuXHJcbiAgLmFwcC1wcm9qZWN0cyB7XHJcbiAgICB0ZXh0LWFsaWduOiBjZW50ZXI7XHJcblxyXG4gICAgLmFwcC1wcm9qZWN0IHtcclxuICAgICAgdGV4dC1hbGlnbjogc3RhcnQ7XHJcbiAgICAgIGRpc3BsYXk6IGlubGluZS1ibG9jaztcclxuICAgICAgcGFkZGluZzogMTBweCAyNXB4IDQwcHg7XHJcbiAgICB9XHJcbiAgfVxyXG59XHJcbiIsIi5hcHAtdmlldy1tb2RlLWJveCB7XG4gIHRleHQtYWxpZ246IGVuZDtcbn1cbi5hcHAtdmlldy1tb2RlLWJveCAuYXBwLXRpdGxlIHtcbiAgbWFyZ2luLXJpZ2h0OiAxMHB4O1xufVxuLmFwcC12aWV3LW1vZGUtYm94IC5hcHAtdmlldy1idXR0b24ge1xuICBwYWRkaW5nOiAwO1xuICB3aWR0aDogMzhweDtcbiAgaGVpZ2h0OiAzOHB4O1xufVxuLmFwcC12aWV3LW1vZGUtYm94IC5hcHAtdmlldy1idXR0b24gbWF0LWljb24ge1xuICBmb250LXNpemU6IDM2cHg7XG4gIHdpZHRoOiAzNnB4O1xuICBoZWlnaHQ6IDM2cHg7XG59XG5cbi5hcHAtcmVzdWx0LW1lc3NhZ2UgLmFwcC1oZWFkZXIge1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIGZvbnQtc2l6ZTogMTZweDtcbiAgbWFyZ2luLWJvdHRvbTogNXB4O1xufVxuLmFwcC1yZXN1bHQtbWVzc2FnZSAuYXBwLWJvZHkge1xuICBmb250LXNpemU6IDE2cHg7XG59XG5cbi5hcHAtbGlzdC12aWV3IHtcbiAgbWFyZ2luOiAwIGF1dG87XG59XG4uYXBwLWxpc3QtdmlldyAuYXBwLWxpc3Qtdmlldy1wcm9qZWN0cyB7XG4gIG1hcmdpbi10b3A6IDMwcHg7XG59XG4uYXBwLWxpc3QtdmlldyAuYXBwLWxpc3Qtdmlldy1wcm9qZWN0cyAuYXBwLXByb2plY3RzLXRhYmxlIHtcbiAgYm9yZGVyLWNvbGxhcHNlOiBjb2xsYXBzZTtcbn1cbi5hcHAtbGlzdC12aWV3IC5hcHAtbGlzdC12aWV3LXByb2plY3RzIC5hcHAtcHJvamVjdHMtdGFibGUgLmFwcC1zb3J0YWJsZS10aCBidXR0b24ge1xuICBmb250LXdlaWdodDogYm9sZDtcbiAgZm9udC1zaXplOiAxNnB4O1xufVxuLmFwcC1saXN0LXZpZXcgLmFwcC1saXN0LXZpZXctcHJvamVjdHMgLmFwcC1wcm9qZWN0cy10YWJsZSAuYXBwLXNvcnRhYmxlLXRoIGkge1xuICB2ZXJ0aWNhbC1hbGlnbjogbWlkZGxlO1xufVxuXG4uYXBwLWdyaWQtdmlldyB7XG4gIG1hcmdpbjogMCBhdXRvO1xufVxuLmFwcC1ncmlkLXZpZXcgLmFwcC1wcm9qZWN0cyB7XG4gIHRleHQtYWxpZ246IGNlbnRlcjtcbn1cbi5hcHAtZ3JpZC12aWV3IC5hcHAtcHJvamVjdHMgLmFwcC1wcm9qZWN0IHtcbiAgdGV4dC1hbGlnbjogc3RhcnQ7XG4gIGRpc3BsYXk6IGlubGluZS1ibG9jaztcbiAgcGFkZGluZzogMTBweCAyNXB4IDQwcHg7XG59Il19 */");

/***/ }),

/***/ "./src/app/pages/projects/projects.component.ts":
/*!******************************************************!*\
  !*** ./src/app/pages/projects/projects.component.ts ***!
  \******************************************************/
/*! exports provided: ProjectsComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectsComponent", function() { return ProjectsComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_material_dialog__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/material/dialog */ "./node_modules/@angular/material/esm2015/dialog.js");
/* harmony import */ var _core_services_api_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../core/services/api.service */ "./src/app/core/services/api.service.ts");
/* harmony import */ var _shared_wait_spinner_wait_spinner_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../../shared/wait-spinner/wait-spinner.component */ "./src/app/shared/wait-spinner/wait-spinner.component.ts");





let ProjectsComponent = class ProjectsComponent {
    constructor(matDialogService, apiService) {
        this.matDialogService = matDialogService;
        this.apiService = apiService;
        this.Ordering = {
            project: 'name',
            creationDate: 'created_on'
        };
        this.isListView = true;
        this.projects = [];
        this.projectsDetails = [];
        this.filter = {
            search: '',
            fromDate: '',
            toDate: '',
            ordering: '',
            asc: true,
            page: 1,
            page_size: 20
        };
    }
    ngOnInit() {
        this.changeViewMode('grid');
    }
    changeViewMode(mode) {
        if (this.viewMode === mode) {
            return;
        }
        this.isListView = mode === 'list';
        this.viewMode = mode;
        this.filter = {
            search: '',
            fromDate: '',
            toDate: '',
            ordering: '',
            asc: true,
            page: 1,
            page_size: this.isListView ? 20 : 'all'
        };
        this.fetchProjects();
    }
    fetchProjects() {
        return tslib__WEBPACK_IMPORTED_MODULE_0__["__awaiter"](this, void 0, void 0, function* () {
            this.dateFilterMessage = undefined;
            this.clearProjects();
            this.closeMessage();
            const dialogRef = this.matDialogService.open(_shared_wait_spinner_wait_spinner_component__WEBPACK_IMPORTED_MODULE_4__["WaitSpinnerComponent"], { disableClose: true });
            try {
                const F = this.filter;
                const pageResult = yield this.apiService.projects__get(F.search, F.fromDate, F.toDate, F.ordering, F.asc, F.page, F.page_size);
                this.setProjects(pageResult);
                if (this.filter.fromDate) {
                    this.dateFilterMessage = `Projects Creation Date Filtered From <b>${this.filter.fromDate}</b> To <b>${this.filter.toDate}</b>`;
                }
            }
            catch (error) {
                this.showMessage({
                    type: 'danger', header: '<strong>Error Fetching Data</strong><hr>',
                    body: 'Something went wrong while fetching your projects.'
                }, 5000);
            }
            finally {
                dialogRef.close();
            }
        });
    }
    setProjects(projectsPageResult) {
        this.projectsPageResult = projectsPageResult;
        this.projects = projectsPageResult.results;
        if (!this.isListView) {
            this.setProjectsDetails();
        }
    }
    clearProjects() {
        this.projectsPageResult = undefined;
        this.projects = [];
        this.projectsDetails = [];
    }
    setProjectsDetails() {
        this.projectsDetails = [];
        for (const project of this.projects) {
            this.projectsDetails.push({
                title: project.name,
                address: {
                    part1: project.address_line_1,
                    part2: `${project.city}, ${project.state}, ${project.zip}`
                },
                estimator: project.estimator,
                tech: project.tech,
                passedSteps: project.passedSteps
            });
        }
    }
    showMessage(message, timeout) {
        this.closeMessage();
        this.resultMessage = message;
        if (timeout) {
            this.resultMessageTimeout = setTimeout(() => this.closeMessage(), timeout);
        }
    }
    closeMessage() {
        clearTimeout(this.resultMessageTimeout);
        this.resultMessage = undefined;
    }
    // app-projects-filter --------------------------------------------------------------------------
    onDateChange(value) {
        // Check if changed
        if (this.filter.fromDate === value.from && this.filter.toDate === value.to) {
            return;
        }
        // Set filter properties
        this.filter.fromDate = value.from;
        this.filter.toDate = value.to;
        this.filter.page = 1;
        // Fetch projects with filter
        this.fetchProjects();
    }
    onSearchChange(value) {
        // Check if changed
        if (this.filter.search === value) {
            return;
        }
        // Set filter properties
        this.filter.search = value;
        this.filter.page = 1;
        // Fetch projects with filter
        this.fetchProjects();
    }
    onPageSizeChange(value) {
        // Check if changed
        if (this.filter.page_size === value) {
            return;
        }
        // Set filter properties
        this.filter.page_size = value;
        this.filter.page = 1;
        // Fetch projects with filter
        this.fetchProjects();
    }
    //-----------------------------------------------------------------------------------------------
    onOrderingChange(ordering) {
        const F = this.filter;
        // Set filter properties
        if (F.ordering === ordering) {
            if (F.asc) {
                F.asc = false;
            }
            else {
                F.ordering = '';
            }
        }
        else {
            F.asc = true;
            F.ordering = ordering;
        }
        // this.filter.page = 1;
        // Fetch projects with filter
        this.fetchProjects();
    }
    onPageChange(pageNumber) {
        // Check if changed
        // Ignore reflection of `this.filter.page = 1;` in other handlers
        if (this.filter.page === pageNumber) {
            return;
        }
        // Set filter properties
        this.filter.page = pageNumber;
        // Fetch projects with filter
        this.fetchProjects();
    }
};
ProjectsComponent.ctorParameters = () => [
    { type: _angular_material_dialog__WEBPACK_IMPORTED_MODULE_2__["MatDialog"] },
    { type: _core_services_api_service__WEBPACK_IMPORTED_MODULE_3__["ApiService"] }
];
ProjectsComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-projects',
        template: tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! raw-loader!./projects.component.html */ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/projects/projects.component.html")).default,
        styles: [tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! ./projects.component.scss */ "./src/app/pages/projects/projects.component.scss")).default]
    })
], ProjectsComponent);



/***/ }),

/***/ "./src/app/pages/projects/projects.module.ts":
/*!***************************************************!*\
  !*** ./src/app/pages/projects/projects.module.ts ***!
  \***************************************************/
/*! exports provided: ProjectsModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ProjectsModule", function() { return ProjectsModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _projects_routing_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./projects-routing.module */ "./src/app/pages/projects/projects-routing.module.ts");
/* harmony import */ var _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../shared/shared.module */ "./src/app/shared/shared.module.ts");
/* harmony import */ var _projects_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./projects.component */ "./src/app/pages/projects/projects.component.ts");
/* harmony import */ var _project_project_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./project/project.component */ "./src/app/pages/projects/project/project.component.ts");
/* harmony import */ var _projects_filter_projects_filter_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./projects-filter/projects-filter.component */ "./src/app/pages/projects/projects-filter/projects-filter.component.ts");







let ProjectsModule = class ProjectsModule {
};
ProjectsModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        declarations: [
            _projects_component__WEBPACK_IMPORTED_MODULE_4__["ProjectsComponent"],
            _project_project_component__WEBPACK_IMPORTED_MODULE_5__["ProjectComponent"],
            _projects_filter_projects_filter_component__WEBPACK_IMPORTED_MODULE_6__["ProjectsFilterComponent"]
        ],
        imports: [
            _projects_routing_module__WEBPACK_IMPORTED_MODULE_2__["ProjectsRoutingModule"],
            _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__["SharedModule"]
        ]
    })
], ProjectsModule);



/***/ })

}]);
//# sourceMappingURL=projects-projects-module.js.map