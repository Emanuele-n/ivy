# global
from numbers import Number
from typing import Union, Optional, Tuple, List, Sequence, Iterable

import paddle

# local
import ivy
from ivy.utils.exceptions import IvyNotImplementedException
from ivy.func_wrapper import with_unsupported_device_and_dtypes

# noinspection PyProtectedMember
from . import backend_version


# Array API Standard #
# -------------------#


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def concat(
    xs: Union[Tuple[paddle.Tensor, ...], List[paddle.Tensor]],
    /,
    *,
    axis: Optional[int] = 0,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    dtypes_list = list(set(map(lambda x: x.dtype, xs)))
    num_dtypes = len(dtypes_list)
    if num_dtypes == 1:
        dtype = dtypes_list[0]
    elif num_dtypes == 2:
        dtype = ivy.promote_types(*dtypes_list)
    else:
        raise ivy.utils.exceptions.IvyException(
            "Tensor list contains more than two dtypes"
        )
    if dtype == "int16":
        xs = [array.cast("int32") for array in xs]
        return paddle.concat(xs, axis).cast("int16")
    else:
        xs = [array.cast(dtype) for array in xs]
        return paddle.concat(xs, axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def expand_dims(
    x: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    axis: Union[int, Sequence[int]] = 0,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if x.dtype == paddle.float16:
        return paddle.unsqueeze(x.cast("float32"), axis).cast(x.dtype)
    return paddle.unsqueeze(x, axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def flip(
    x: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    axis: Optional[Union[int, Sequence[int]]] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if axis is None:
        axis = list(range(x.ndim))
    if x.dtype in [paddle.int8, paddle.int16, paddle.uint8, paddle.float16]:
        return paddle.flip(x.cast("float32"), axis).cast(x.dtype)
    return paddle.flip(x, axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def permute_dims(
    x: paddle.Tensor,
    /,
    axes: Tuple[int, ...],
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if x.dtype in [paddle.int8, paddle.int16, paddle.uint8]:
        return paddle.transpose(x.cast("float32"), axes).cast(x.dtype)
    return paddle.transpose(x, axes)


def _reshape_fortran_paddle(x, shape):
    with ivy.ArrayMode(False):
        if len(x.shape) > 0:
            x = permute_dims(x, list(reversed(range(len(x.shape)))))
        return permute_dims(
            paddle.reshape(x, shape[::-1]), list(range(len(shape)))[::-1]
        )


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def reshape(
    x: paddle.Tensor,
    /,
    shape: Union[ivy.NativeShape, Sequence[int]],
    *,
    copy: Optional[bool] = None,
    order: Optional[str] = "C",
    allowzero: Optional[bool] = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if len(shape) == 0:
        out_scalar = True
        shape = [1]
    else:
        out_scalar = False
    if len(x.shape) == 0:
        x = paddle.reshape(x, shape=[1])
    if not allowzero:
        shape = [
            new_s if con else old_s
            for new_s, con, old_s in zip(shape, paddle.to_tensor(shape) != 0, x.shape)
        ]
    if copy:
        newarr = paddle.clone(x)
        if order == "F":
            ret = _reshape_fortran_paddle(newarr, shape)
            if out_scalar:
                return ivy.to_native(squeeze(ret, 0))

            return ret
        ret = paddle.reshape(newarr, shape)
        if out_scalar:
            return ivy.to_native(squeeze(ret, 0))

        return ret
    if order == "F":
        ret = _reshape_fortran_paddle(x, shape)
        if out_scalar:
            return ivy.to_native(squeeze(ret, 0))

        return ret
    ret = paddle.reshape(x, shape)
    if out_scalar:
        return ivy.to_native(squeeze(ret, 0))

    return ret


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}},
    backend_version,
)
def roll(
    x: paddle.Tensor,
    /,
    shift: Union[int, Sequence[int]],
    *,
    axis: Optional[Union[int, Sequence[int]]] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.bool,
    ]:
        return paddle.roll(x.cast("float32"), shift, axis).cast(x.dtype)
    return paddle.roll(x, shift, axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def squeeze(
    x: paddle.Tensor,
    /,
    axis: Union[int, Sequence[int]],
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if isinstance(axis, list):
        axis = tuple(axis)
    if len(x.shape) == 0:
        if axis is None or axis == 0 or axis == -1:
            return x
        raise ivy.utils.exceptions.IvyException(
            "tried to squeeze a zero-dimensional input by axis {}".format(axis)
        )
    if x.dtype in [paddle.int16, paddle.float16]:
        return paddle.squeeze(x.cast("float32"), axis=axis).cast(x.dtype)
    return paddle.squeeze(x, axis=axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def stack(
    arrays: Union[Tuple[paddle.Tensor], List[paddle.Tensor]],
    /,
    *,
    axis: int = 0,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    # The input list converted to a tensor to ensure matching dtype of elements.
    # Because stack function does not support mixed dtypes.
    dtype_list = set(map(lambda x: x.dtype, arrays))
    if len(dtype_list) == 1:
        dtype = dtype_list.pop()
    elif len(dtype_list) == 2:
        dtype = ivy.promote_types(*dtype_list)
    else:
        raise ValueError("Cannot promote more than 2 dtypes per stack.")

    arrays = list(map(lambda x: x.cast(dtype), arrays))

    if dtype in [paddle.int8, paddle.int16, paddle.uint8, paddle.float16, paddle.bool]:
        arrays = list(map(lambda x: x.cast("float32"), arrays))
        return paddle.stack(arrays, axis=axis).cast(dtype)

    elif dtype in [
        paddle.complex64,
        paddle.complex128,
    ]:
        arrays = list(map(lambda x: x.cast(dtype), arrays))
        real_list = list(map(lambda x: x.real(), arrays))
        imag_list = list(map(lambda x: x.imag(), arrays))
        re_stacked = paddle.stack(real_list, axis=axis)
        imag_stacked = paddle.stack(imag_list, axis=axis)
        return re_stacked + imag_stacked * 1j
    else:
        arrays = list(map(lambda x: x.cast(dtype), arrays))
        return paddle.stack(arrays, axis=axis)


# Extra #
# ------#


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}},
    backend_version,
)
def split(
    x: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    num_or_size_splits: Optional[Union[int, List[int]]] = None,
    axis: Optional[int] = 0,
    with_remainder: Optional[bool] = False,
) -> List[paddle.Tensor]:
    if x.shape == ():
        if num_or_size_splits is not None and num_or_size_splits != 1:
            raise ivy.utils.exceptions.IvyException(
                "input array had no shape, but num_sections specified was {}".format(
                    num_or_size_splits
                )
            )
        return [x]
    if num_or_size_splits is None:
        num_or_size_splits = x.shape[axis]
    elif isinstance(num_or_size_splits, int):
        num_chunks = x.shape[axis] // num_or_size_splits
        remainder = x.shape[axis] % num_or_size_splits
        if remainder != 0:
            if with_remainder:
                num_or_size_splits = [num_or_size_splits] * num_chunks + [remainder]
            else:
                raise ivy.utils.exceptions.IvyException(
                    "Split size is not compatible with input shape"
                )

    if isinstance(num_or_size_splits, (list, tuple)):
        if sum(num_or_size_splits) < x.shape[axis]:
            num_or_size_splits + type(num_or_size_splits)([-1])
        elif sum(num_or_size_splits) > x.shape[axis]:
            raise ivy.utils.exceptions.IvyException(
                f"total split size is not compatible with input shape,"
                f" got {sum(num_or_size_splits)} which is more than x.shape[axis]"
            )

    if x.dtype in [paddle.int16, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x):
            imag_list = paddle.split(x.imag(), num_or_size_splits, axis)
            real_list = paddle.split(x.real(), num_or_size_splits, axis)
            return [(a + b * 1j) for a, b in zip(real_list, imag_list)]
        ret = paddle.split(x.cast("int32"), num_or_size_splits, axis)
        return [tensor.cast(x.dtype) for tensor in ret]
    return paddle.split(x, num_or_size_splits, axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def repeat(
    x: paddle.Tensor,
    /,
    repeats: Union[int, Iterable[int]],
    *,
    axis: int = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if isinstance(repeats, Number) and repeats == 0:
        return paddle.to_tensor([], dtype=x.dtype)
    elif isinstance(repeats, paddle.Tensor):
        if max(repeats.shape) == 1:
            repeats = repeats.item()
            if repeats == 0:
                return paddle.to_tensor([], dtype=x.dtype)
    if axis is not None:
        axis = axis % x.ndim
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle.repeat_interleave(
                x.real(), repeats=repeats, axis=axis
            ) + 1j * paddle.repeat_interleave(x.imag(), repeats=repeats, axis=axis)

        return paddle.repeat_interleave(
            x.cast("float32"), repeats=repeats, axis=axis
        ).cast(x.dtype)

    return paddle.repeat_interleave(x, repeats=repeats, axis=axis)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def tile(
    x: paddle.Tensor, /, repeats: Sequence[int], *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if ivy.min(repeats) == 0:
        # This logic is to mimic other backends behaviour when a 0 in repeat
        # is received since paddle doesn't natively support it
        if len(repeats) < x.ndim:
            shape = x.shape
            shape[-len(repeat) :] = ivy.multiply(
                shape[-len(repeat) :], repeats
            ).to_list()
        elif len(repeats) > x.ndim:
            shape = repeats
            shape[-x.ndim :] = ivy.multiply(shape[-x.ndim :], repeats).to_list()
        else:
            shape = ivy.multiply(x.shape, repeats).to_list()
        return paddle.zeros(shape).cast(x.dtype)

    if x.dtype in [paddle.int8, paddle.int16, paddle.uint8, paddle.float16]:
        return paddle.tile(x.cast("float32"), repeats).cast(x.dtype)
    return paddle.tile(x, repeats)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def constant_pad(
    x: paddle.Tensor,
    /,
    pad_width: List[List[int]],
    *,
    value: Number = 0.0,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    paddings = []
    pad_width = list(pad_width)
    for item in pad_width:
        if len(item) != 2:
            raise ivy.utils.exceptions.IvyException("Length of each item should be 2")
        else:
            paddings.append(item[0])
            paddings.append(item[1])
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.bool,
    ]:
        return paddle.nn.functional.pad(
            x.cast("float32"), pad=paddings, value=value
        ).cast(x.dtype)
    return paddle.nn.functional.pad(x=x, pad=paddings, value=value)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def zero_pad(
    x: paddle.Tensor,
    /,
    pad_width: List[List[int]],
    *,
    out: Optional[paddle.Tensor] = None,
):
    with ivy.ArrayMode(False):
        return constant_pad(x, pad_width=pad_width, value=0)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def swapaxes(
    x: paddle.Tensor,
    axis0: int,
    axis1: int,
    /,
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    axes = [x for x in range(x.ndim)]
    axes[axis0], axes[axis1] = axes[axis1], axes[axis0]
    with ivy.ArrayMode(False):
        return permute_dims(x, axes)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def clip(
    x: paddle.Tensor,
    x_min: Union[Number, paddle.Tensor],
    x_max: Union[Number, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    with ivy.ArrayMode(False):
        return ivy.minimum(ivy.maximum(x, x_min), x_max)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def unstack(
    x: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    axis: int = 0,
    keepdims: bool = False,
) -> List[paddle.Tensor]:
    if x.ndim == 0:
        return [x]
    if axis is not None:
        axis = axis % x.ndim
    else:
        axis = 0
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            real_list = paddle.unbind(x.real(), axis)
            imag_list = paddle.unbind(x.imag(), axis)
            ret = [(a + 1j * b) for a, b in zip(real_list, imag_list)]
        else:
            ret = paddle.unbind(x.cast("float32"), axis)
            ret = list(map(lambda a: a.cast(x.dtype), ret))

    else:
        ret = paddle.unbind(x, axis)
    if keepdims:
        with ivy.ArrayMode(False):
            return [ivy.expand_dims(r, axis=axis) for r in ret]
    return ret
