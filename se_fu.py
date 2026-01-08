# configs/example/se_fu.py
#
# Run a RISC-V SE workload on DerivO3CPU with a configurable functional-unit pool.
#
# Example:
# build/RISCV/gem5.opt -d m5out \
#   configs/example/se_fu.py --cmd=program.riscv --caches \
#   --ialu=4 --imult=1 --fpalu=4 --fpmult=1 --memport=2

import argparse
import m5
from m5.objects import (
    System, Root, Process, SEWorkload,
    SrcClockDomain, VoltageDomain, AddrRange,
    DerivO3CPU, TimingSimpleCPU,
    SystemXBar, MemCtrl, DDR3_1600_8x8,
    Cache, L2XBar,
    FUPool, FUDesc, OpDesc
)

# ----------------------------
# Minimal caches
# ----------------------------
class L1ICache(Cache):
    size = "32kB"
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 8
    is_read_only = True

class L1DCache(Cache):
    size = "32kB"
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 8
    tgts_per_mshr = 8

class L2Cache(Cache):
    size = "256kB"
    assoc = 8
    tag_latency = 10
    data_latency = 10
    response_latency = 10
    mshrs = 16
    tgts_per_mshr = 12


def build_fu_pool(ialu: int, imult: int, fpalu: int, fpmult: int, memport: int) -> FUPool:
    """
    Build FU pool for DerivO3CPU.
    opClass names may vary across gem5 versions; adjust if your build errors.
    """

    class IntALU(FUDesc):
        count = ialu
        opList = [OpDesc(opClass="IntAlu", opLat=1)]

    class IntMultDiv(FUDesc):
        count = imult
        opList = [
            OpDesc(opClass="IntMult", opLat=3),
            OpDesc(opClass="IntDiv",  opLat=12),
        ]

    class FPALU(FUDesc):
        count = fpalu
        opList = [
            OpDesc(opClass="FloatAdd", opLat=2),
            OpDesc(opClass="FloatCmp", opLat=2),
            OpDesc(opClass="FloatCvt", opLat=2),
        ]

    class FPMultDiv(FUDesc):
        count = fpmult
        opList = [
            OpDesc(opClass="FloatMult", opLat=4),
            OpDesc(opClass="FloatDiv",  opLat=12),
        ]

    class MemPort(FUDesc):
        count = memport
        opList = [
            OpDesc(opClass="MemRead",  opLat=1),
            OpDesc(opClass="MemWrite", opLat=1),
        ]

    return FUPool(FUList=[IntALU(), IntMultDiv(), FPALU(), FPMultDiv(), MemPort()])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help="RISC-V binary to run (static recommended)")
    ap.add_argument("--args", default="", help="Arguments to pass to program (single string)")
    ap.add_argument("--cpu-type", choices=["O3", "TimingSimple"], default="O3")
    ap.add_argument("--cpu-clock", default="1GHz")
    ap.add_argument("--mem-size", default="2GB")
    ap.add_argument("--caches", action="store_true", help="Enable simple private L1 + shared L2")

    # FU knobs
    ap.add_argument("--ialu", type=int, default=4)
    ap.add_argument("--imult", type=int, default=1)
    ap.add_argument("--fpalu", type=int, default=1)
    ap.add_argument("--fpmult", type=int, default=1)
    ap.add_argument("--memport", type=int, default=2)

    args = ap.parse_args()

    system = System()
    system.clk_domain = SrcClockDomain(clock=args.cpu_clock, voltage_domain=VoltageDomain())
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange(args.mem_size)]

    # CPU
    if args.cpu_type == "O3":
        system.cpu = DerivO3CPU()
        system.cpu.fuPool = build_fu_pool(args.ialu, args.imult, args.fpalu, args.fpmult, args.memport)
    else:
        system.cpu = TimingSimpleCPU()

    # Buses + memory
    system.membus = SystemXBar()
    system.system_port = system.membus.cpu_side_ports

    if args.caches:
        system.cpu.icache = L1ICache()
        system.cpu.dcache = L1DCache()
        system.l2bus = L2XBar()
        system.l2cache = L2Cache()

        system.cpu.icache.connectCPU(system.cpu)
        system.cpu.dcache.connectCPU(system.cpu)

        system.cpu.icache.connectBus(system.l2bus)
        system.cpu.dcache.connectBus(system.l2bus)

        system.l2cache.connectCPUSideBus(system.l2bus)
        system.l2cache.connectMemSideBus(system.membus)
    else:
        system.cpu.icache = None
        system.cpu.dcache = None

    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports

    # Workload (SE)
    process = Process()
    process.cmd = [args.cmd] + (args.args.split() if args.args else [])
    system.cpu.workload = process
    system.cpu.createThreads()

    root = Root(full_system=False, system=system)
    m5.instantiate()
    exit_event = m5.simulate()
    print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")

if __name__ == "__main__":
    main()
