{
    'name': 'User Login Time Restriction',
    'version': '19.0.3.0.0',
    'summary': 'Dynamic login time restrictions using groups and DB-configured hours',
    'description': """
        Fully dynamic login restriction module:
        - Configure start/end time (IST or any timezone) from Settings UI
        - Assign any security group as the "restricted" group
        - Three-layer enforcement: login hook + HTTP middleware + cron job
        - Browser watchdog shows red banner and redirects on session termination
    """,
    'category': 'Security',
    'author': 'Custom',
    'depends': ['base', 'web'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_users_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'login_restriction/static/src/js/session_watchdog.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
