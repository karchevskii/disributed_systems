from typing import Annotated
from fastapi import APIRouter

from webauthn import generate_registration_options
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

@router.get(
    "/me",
    response_model=UserRelDTO,
    description="Get the current user",
)
async def get_user(
    uow: UOWDep,
    current_user: Annotated[UserDTO, Depends(get_current_user)],
):
    user = await UsersService().get_user_rel(uow=uow, filters={"id": current_user.id})
    return user


@router.patch(
    "/me",
    response_model=UserDTO,
    description="Update the current user",
)
async def update_user(
    user: UserUpdateSchema,
    uow: UOWDep,
    current_user: Annotated[UserDTO, Depends(get_current_user)],
):
    updated_user = await UsersService().update_user(uow=uow, user_id=current_user.id, user=user)
    return updated_user


@router.post(
    "/register",
)
async def register_user(
    user: UserCreateSchema,
    uow: UOWDep,
):
    user = await UsersService().create_user(uow=uow, user=user)
    reg_options = generate_registration_options(
        rp_id="localhost",
        rp_name="TicTacToe",
        user_id=user.id,
        user_name=user.username,
    )




# Simple Options
simple_registration_options = generate_registration_options(
    rp_id="example.com",
    rp_name="Example Co",
    user_name="bob",
)

# Complex Options
complex_registration_options = generate_registration_options(
    rp_id="example.com",
    rp_name="Example Co",
    user_id=bytes([1, 2, 3, 4]),
    user_name="Lee",
    attestation=AttestationConveyancePreference.DIRECT,
    authenticator_selection=AuthenticatorSelectionCriteria(
        authenticator_attachment=AuthenticatorAttachment.PLATFORM,
        resident_key=ResidentKeyRequirement.REQUIRED,
    ),
    challenge=bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 0]),
    exclude_credentials=[
        PublicKeyCredentialDescriptor(
            id=b"1234567890",
            transports=[
                AuthenticatorTransport.INTERNAL,
                AuthenticatorTransport.HYBRID,
            ]
        ),
    ],
    supported_pub_key_algs=[COSEAlgorithmIdentifier.ECDSA_SHA_512],
    timeout=12000,
)