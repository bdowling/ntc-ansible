#!usr/bin/env python

import ansible.runner
import json
import sys

def compare(list_one, list_two):
    msg = ''
    for el in list_one:
        if el not in list_two:
            msg = str(el) + " is not found in sample input"
            return 1,msg
    return 0,msg

if __name__ == "__main__":

    HOSTS = 'hosts'

    runner = ansible.runner.Runner(
       module_name='get_test_info',
       module_args='',
       pattern='localhost'
       hosts_list=HOSTS
    )

    results = runner.run()

    tests = results['contacted']['localhost']['tests']


    responses = []
    for test_case in tests:
        filepath = test_case.get('path')
        rawfile = test_case.get('rawfile')
        platform = test_case.get('platform')
        command = test_case.get('command')

        args = dict(file=filepath + '/' + rawfile, platform=platform,
                    command=command, connection='offline')
        runner = ansible.runner.Runner(
        module_name='ntc_show_command',
        module_args=args,
        pattern='localhost'
        hosts_list=HOSTS
        )
        results = runner.run()

        responses.append(results)

    # print json.dumps(responses, indent=4)
    with_parsed = []

    for rsp in responses:
        # print json.dumps(rsp, indent=4)
        # print rsp['contacted']['localhost']['invocation']['module_args']
        args = rsp['contacted']['localhost']['invocation']['module_args']
        split = args.split(' ')
        for each in split:
            if '.raw' in each:
                parsed = each.replace('.raw', '.parsed')
                parsed = parsed.lstrip('file=')

                runner = ansible.runner.Runner(
                    module_name='include_vars',
                    module_args=parsed,
                    pattern='localhost'
                    hosts_list=HOSTS
                )
                results = runner.run()
                results['response'] = rsp['contacted']['localhost']['response']
                # print rsp.get('response')
                with_parsed.append(results)

    #    print json.dumps(with_parsed, indent=4)

    for each in with_parsed:
        text = each['contacted']['localhost']['invocation']['module_args']
        command = text.split('/')[-1].split('.')[0]
        parsed_sample = each['contacted']['localhost']['ansible_facts']['parsed_sample']
        result = each['response']

        rc,msg = compare(result, parsed_sample)
        failed = False
        print command
        if rc != 0:
            print '----> failed'
            print 'msg:'
            print msg
            print '*' * 100
            print 'parsed (from parsed file): '
            print parsed_sample
            print '*' * 100
            print 'result (from ntc_show_command): '
            print result
            failed = True
        else:
            print '----> passed'
        print '=' * 50

    if failed:
        sys.exit(1)
    else:
        sys.exit(0)