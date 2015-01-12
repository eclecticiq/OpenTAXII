import os
import yaml
import ConfigParser
import logging

from .taxii.bindings import ContentBinding

log = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.realpath(__file__))

class IniConfig(ConfigParser.RawConfigParser):

    @property
    def services(self):
        services = []
        for section in self.sections():
            if section.startswith('service:'):
                type, id = section.replace('service:', '').split(':')
                services.append((type, id, section))
                
        return services

    @property
    def db_connection(self):
        return self.safe_get('server', 'db_connection')


    @property
    def logging_config(self):
        path = self.get('server', 'logging_config')

        if not path:
            return None

        if os.path.exists(path):
            full_path = path
        else:
            full_path = os.path.join(current_dir, path)

        if not os.path.exists(full_path):
            raise ValueError('Can not read logging configuration file at %s' % full_path)

        with open(full_path, 'r') as f:
            return yaml.load(f)

    @property
    def storage_hooks(self):
        return self.get_list('server', 'storage_hooks')

    @property
    def domain(self):
        return self.safe_get('server', 'domain')

    def inbox_options(self, section):
        defaults = 'defaults:inbox'
        options = dict(self.items(defaults))
        options.update(dict(self.items(section)))

        options['accept_all_content'] = boolean(options['accept_all_content'])
        options['supported_content'] = [ContentBinding(binding=b, subtypes=None) for b in string_list(options['supported_content'])]
        options['destination_collection_required'] = boolean(options['destination_collection_required'])

        return options

    def discovery_options(self, section):
        defaults = 'defaults:discovery'
        options = dict(self.items(defaults))
        options.update(dict(self.items(section)))
        options['advertised_services'] = string_list(options['advertised_services'])

        return options


    def safe_get(self, section, option, defaults=None, default_value=None):
        try:
            return self.get(section, option)
        except ConfigParser.NoOptionError:
            return self.get(defaults, option) if defaults else default_value


    def get_list(self, section, option, defaults=None, default_value=''):
        return string_list(self.safe_get(section, option, defaults=defaults, default_value=default_value))
                
    def get_boolean(self, section, option, defaults=None, default_value=None):
        return boolean(self.safe_get(section, option, defaults=defaults, default_value=default_value))


def load_config(base_config, optional_env_var):

    config = IniConfig()
    config.readfp(open(os.path.join(current_dir, base_config)))

    log.info('Loaded basic config from %s' % base_config)

    env_var_conf = os.environ.get(optional_env_var)

    if env_var_conf:
        if not config.read(env_var_conf):
            raise RuntimeError('Can not load configuration from the path configured in the '
                    'environment variable: %s = %s' % (optional_env_var, env_var_conf))
        else:
            log.info('Loaded a config from %s' % env_var_conf)

    return config


TRUTHY_STRINGS = ('yes', 'true', 'on', '1')
FALSY_STRINGS  = ('no', 'false', 'off', '0')

def boolean(s):
    ss = str(s).lower()
    if ss in TRUTHY_STRINGS:
        return True
    elif ss in FALSY_STRINGS:
        return False
    else:
        raise ValueError("not a valid boolean value: " + repr(s))

def string_list(s):
    if not s:
        return []
    return map(lambda x: x.strip(), s.split(','))
