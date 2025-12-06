from __future__ import annotations

from typing import Dict

from actions.registry import ActionRegistry
from protocol.xmodem import XMODEMPacketBuilder
from utils.file_utils import get_file_meta, read_block


def send_xmodem_block(ctx, args: Dict[str, object]):
    meta = get_file_meta(ctx)
    block = int(ctx.eval_value(args.get("block", 1)))
    data = read_block(meta["path"], block, 128)
    packet = XMODEMPacketBuilder.build_block(block, data)
    ctx.channel_write(packet)
    ctx.set_var("last_sent_block", block)


def send_eot(ctx, args: Dict[str, object]):
    ctx.channel_write(XMODEMPacketBuilder.build_eot())


def register_protocol_actions():
    ActionRegistry.register("send_xmodem_block", send_xmodem_block)
    ActionRegistry.register("send_eot", send_eot)
