"""Sequential Guild -> Board test v0.10. Home and MVP are not run."""
import argparse
from datetime import datetime, timezone
import json
from detect_activity import ROOT
import run_guild
import run_board


def run_sequence(timeout, guild_runner, board_runner, progress):
    progress('guild_running')
    guild=guild_runner(['--run','--timeout',str(timeout)])
    if not guild or guild.get('state')!='completed' or guild.get('completion_verified') is not True:
        raise RuntimeError('Guild completion not verified; Board was not started.')
    if not guild.get('foreground'):
        raise RuntimeError('Guild foreground handle missing; Board was not started.')
    progress('guild_completed_board_running')
    board=board_runner(['--run','--timeout',str(timeout),'--reopen-activity'],
                       expected_foreground=guild['foreground'],start_delay=0)
    if not board or board.get('state')!='completed' or board.get('completion_verified') is not True:
        raise RuntimeError('Board completion not verified.')
    progress('completed')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true')
    p.add_argument('--timeout',type=int,default=1800,help='Timeout per workflow in seconds')
    a=p.parse_args()
    if a.timeout<=0: p.error('--timeout must be positive')
    if not a.run:
        print('READ ONLY: checking Guild on current screen; no sequence will start.')
        run_guild.main([])
        print('Use run_daily.py --run for Activity -> Guild -> Activity -> Board.')
        return
    last='starting'
    def progress(state,error=None):
        nonlocal last
        last=state
        folder=ROOT/'captures'; folder.mkdir(exist_ok=True)
        data={'state':state,'completion_verified':state=='completed',
              'time_utc':datetime.now(timezone.utc).isoformat(),'error':error}
        (folder/'daily_run_result.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print('Daily sequence:',state,flush=True)
    try:
        run_sequence(a.timeout,run_guild.main,run_board.main,progress)
    except (Exception,KeyboardInterrupt) as error:
        phase=last
        progress('stopped_unverified',f'{phase}: {error}')
        raise


if __name__=='__main__': main()
