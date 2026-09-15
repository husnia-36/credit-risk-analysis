"""
Part 8: REST API exposing the lending decision prototype.

Endpoints:
  POST /api/v1/lending/decision                -- full pipeline, returns + stores a decision
  POST /api/v1/lending/affordability            -- affordability-only calculator (no model call)
  GET  /api/v1/lending/decisions/{applicationId} -- retrieve a previously made decision
  GET  /api/v1/models/current                    -- current model + policy version info
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.affordability import assess_affordability
from src.decision import ApplicationValidationError, evaluate_application
from src.model_features import MissingModelFieldError
from src.model_loader import model_status
from src.policy import load_policy

app = FastAPI(title="Lending Decision Prototype", version="1.0")

_POLICY = load_policy()
_DECISIONS: dict[str, dict] = {}  # in-memory store, applicationId -> decision result


class LoanApplicationRequest(BaseModel):
    customerId: str
    monthlyIncome: float = Field(gt=0, description="Monthly income, must be positive")
    existingMonthlyDebt: float = Field(ge=0, description="Existing monthly debt obligations")
    requestedAmount: float = Field(gt=0, description="Requested loan principal")
    requestedTenure: int = Field(gt=0, description="Requested tenure in months")

    # Raw risk-model fields (same 8 required + 2 optional fields as Assignment 1's API)
    revolving_utilization: float = Field(ge=0)
    age: int = Field(gt=0)
    late_30_59: float = Field(ge=0)
    debt_ratio: float = Field(ge=0)
    open_credit_lines: int = Field(ge=0)
    late_90_plus: float = Field(ge=0)
    real_estate_loans: int = Field(ge=0)
    late_60_89: float = Field(ge=0)
    dependents: Optional[float] = Field(default=None, ge=0)


class AffordabilityRequest(BaseModel):
    monthlyIncome: float = Field(gt=0)
    existingMonthlyDebt: float = Field(ge=0)
    requestedAmount: float = Field(gt=0)
    requestedTenure: int = Field(gt=0)


@app.exception_handler(ApplicationValidationError)
@app.exception_handler(MissingModelFieldError)
async def _validation_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "VALIDATION_ERROR", "detail": str(exc)})


@app.post("/api/v1/lending/decision")
def make_decision(application: LoanApplicationRequest):
    result = evaluate_application(application.model_dump())
    application_id = str(uuid.uuid4())
    result = {"applicationId": application_id, **result}
    _DECISIONS[application_id] = result
    return result


@app.post("/api/v1/lending/affordability")
def check_affordability(request: AffordabilityRequest):
    return assess_affordability(
        monthly_income=request.monthlyIncome,
        existing_monthly_debt=request.existingMonthlyDebt,
        requested_amount=request.requestedAmount,
        requested_tenure=request.requestedTenure,
        annual_rate=_POLICY["pricing"]["annualInterestRate"],
        max_allowed_dti=_POLICY["affordability"]["maxAllowedDTI"],
        defined_expenses=_POLICY["affordability"]["definedExpenses"],
    )


@app.get("/api/v1/lending/decisions/{application_id}")
def get_decision(application_id: str):
    result = _DECISIONS.get(application_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No decision found for applicationId {application_id!r}")
    return result


@app.get("/api/v1/models/current")
def get_current_model():
    return {**model_status(), "policyVersion": _POLICY["policyVersion"]}
