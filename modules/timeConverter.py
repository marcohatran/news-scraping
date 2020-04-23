from datetime import datetime, timedelta
import re


def timestamp_converter(ld_dict):
    date_published = ld_dict.get('datePublished')
    date_modified = ld_dict.get('dateModified')
    oldFormat = "%m/%d/%Y %I:%M:%S %p"
    try:
        date_published = datetime.strptime(date_published, oldFormat)
        date_published = datetime.timestamp(date_published)

        date_modified = datetime.strptime(date_modified, oldFormat)
        date_modified = datetime.timestamp(date_modified)

        ld_dict['datePublished'] = date_published
        ld_dict['dateModified'] = date_modified

        return ld_dict
    except:
        oldFormat = "%Y-%m-%dT%H:%M:%S%z"
        if "+07:00" in date_published:
            date_published = date_published.replace('+07:00', '+0700')
        if "+07:00" in date_modified:
            date_modified = date_modified.replace('+07:00', '+0700')
        if "+08:00" in date_published:
            date_published = date_published.replace('+08:00', '+0800')
        if "+08:00" in date_modified:
            date_modified = date_modified.replace('+08:00', '+0800')

        try:
            date_published = datetime.strptime(date_published, oldFormat)
            date_published = datetime.timestamp(date_published)

            date_modified = datetime.strptime(date_modified, oldFormat)
            date_modified = datetime.timestamp(date_modified)

            ld_dict['datePublished'] = date_published
            ld_dict['dateModified'] = date_modified

            return ld_dict
        except:
            oldFormat = "%Y-%m-%dT%H:%M:%S"
            if "." in date_published and "." in date_modified:
                date_published, frag = date_published.split('.')
                date_modified, frag = date_modified.split('.')
            try:
                date_published = datetime.strptime(date_published, oldFormat)
                date_published = datetime.timestamp(date_published)

                date_modified = datetime.strptime(date_modified, oldFormat)
                date_modified = datetime.timestamp(date_modified)

                ld_dict['datePublished'] = date_published
                ld_dict['dateModified'] = date_modified

                return ld_dict
            except:
                oldFormat = "%Y-%m-%d"
                try:
                    date_published = datetime.strptime(
                        date_published, oldFormat)
                    date_published = datetime.timestamp(date_published)

                    date_modified = datetime.strptime(date_modified, oldFormat)
                    date_modified = datetime.timestamp(date_modified)

                    ld_dict['datePublished'] = date_published
                    ld_dict['dateModified'] = date_modified

                    return ld_dict
                except Exception as e:
                    print(e)


def vietnamnet_timestamp(ld_dict):
    oldFormat = "%d-%m-%YT%H:%M:%S%z"
    date_published = ld_dict.get('datePublished')
    date_modified = ld_dict.get('dateModified')

    if "+07:00" in date_published:
        date_published = date_published.replace('+07:00', '+0700')
    if "+07:00" in date_modified:
        date_modified = date_modified.replace('+07:00', '+0700')

    try:
        date_published = datetime.strptime(date_published, oldFormat)
        date_published = datetime.timestamp(date_published)

        date_modified = datetime.strptime(date_modified, oldFormat)
        date_modified = datetime.timestamp(date_modified)

        ld_dict['datePublished'] = date_published
        ld_dict['dateModified'] = date_modified

        return ld_dict
    except Exception as e:
        print(e)


def Yeah1_timestamp(time):
    oldFormat = "%Y-%m-%dT%H:%M:%S%z"
    if "+07:00" in time:
        time = time.replace('+07:00', '+0700')
    if "+08:00" in time:
        time = time.replace('+08:00', '+0800')

    time = datetime.strptime(time, oldFormat)
    time = datetime.timestamp(time)
    return time


def Dspl_timestamp(time):
    time1 = ""
    if 'Thứ hai' in time:
        time1 = time.replace('Thứ hai, ', '')
    if 'Thứ ba' in time:
        time1 = time.replace('Thứ ba, ', '')
    if 'Thứ tư' in time:
        time1 = time.replace('Thứ tư, ', '')
    if 'Thứ năm' in time:
        time1 = time.replace('Thứ năm, ', '')
    if 'Thứ sáu' in time:
        time1 = time.replace('Thứ sáu, ', '')
    if 'Thứ bảy' in time:
        time1 = time.replace('Thứ bảy, ', '')
    if 'Chủ nhật' in time:
        time1 = time.replace('Chủ nhật, ', '')
    oldFormat = "%d/%m/%Y | %H:%M"
    if 'GMT+7' in time1:
        time1 = time1.replace(' GMT+7', '')
    time1 = datetime.strptime(time1, oldFormat)
    time1 = datetime.timestamp(time1)
    return time1


def Tiin_timestamp(time):
    oldFormat = "%d/%m/%Y %H:%M"
    time = datetime.strptime(time, oldFormat)
    time = datetime.timestamp(time)
    return time


def Vnex_timestamp(time):
    oldFormat = "%Y-%m-%dT%H:%M:%S%z"
    try:
        if "+07:00" in time:
            time = time.replace('+07:00', '+0700')
        if "+08:00" in time:
            time = time.replace('+08:00', '+0800')
        time = datetime.strptime(time, oldFormat)
        time = datetime.timestamp(time)
        return time
    except:
        time1 = ""
        if 'Thứ hai' in time:
            time1 = time.replace('Thứ hai, ', '')
        if 'Thứ ba' in time:
            time1 = time.replace('Thứ ba, ', '')
        if 'Thứ tư' in time:
            time1 = time.replace('Thứ tư, ', '')
        if 'Thứ năm' in time:
            time1 = time.replace('Thứ năm, ', '')
        if 'Thứ sáu' in time:
            time1 = time.replace('Thứ sáu, ', '')
        if 'Thứ bảy' in time:
            time1 = time.replace('Thứ bảy, ', '')
        if 'Chủ nhật' in time:
            time1 = time.replace('Chủ nhật, ', '')
        oldFormat = "%d/%m/%Y, %H:%M"
        if '(GMT+7)' in time1:
            time1 = time1.replace(' GMT+7', '')
        time1 = datetime.strptime(time1, oldFormat)
        time1 = datetime.timestamp(time1)
        return time1


def comment_time(time):
    oldFormat = "%H:%M | %d/%m/%Y"

    try:
        newTime = datetime.strptime(time, oldFormat)
        newTime = datetime.timestamp(newTime)
        return newTime
    except:
        if 'Thứ hai' in time:
            time.replace(' Thứ hai', '')
            commentDay = 0
        if 'Thứ ba' in time:
            time.replace('Thứ ba', '')
            commentDay = 1
        if 'Thứ tư' in time:
            time.replace('Thứ tư', '')
            commentDay = 2
        if 'Thứ năm' in time:
            time.replace('Thứ năm', '')
            commentDay = 3
        if 'Thứ sáu' in time:
            time.replace('Thứ sáu', '')
            commentDay = 4
        if 'Thứ bảy' in time:
            time.replace('Thứ bảy', '')
            commentDay = 5
        if 'Chủ nhật' in time:
            time.replace('Chủ nhật', '')
            commentDay = 6
        oldFormat = "%H:%M "
        try:
            day = datetime.today() - timedelta(datetime.today().weekday() - commentDay)
            newTime = datetime.strptime(time, oldFormat)
            newTime = newTime.replace(
                year=day.year, month=day.month, day=day.day)
            newTime = datetime.timestamp(newTime)
            return newTime
        except:
            if "." in time:
                time, frag = time.split('.')
            oldFormat = "%Y-%m-%dT%H:%M:%S"
            try:
                newTime = datetime.strptime(time, oldFormat)
                newTime = datetime.timestamp(newTime)
                return newTime
            except:
                if "+07:00" in time:
                    time = time.replace("+07:00", "+0700")
                oldFormat = "%Y-%m-%dT%H:%M:%S%z"
                try:
                    newTime = datetime.strptime(time, oldFormat)
                    newTime = datetime.timestamp(newTime)
                    return newTime
                except:
                    oldFormat = "%Hh%M, ngày %d-%m-%Y"
                    try:
                        newTime = datetime.strptime(time, oldFormat)
                        newTime = datetime.timestamp(newTime)
                        return newTime
                    except:
                        newTime = None
                        if "phút trước" in time:
                            strings = [s for s in time.split() if s.isdigit()]
                            time = strings[0]
                            time = int(time)
                            newTime = datetime.now() - timedelta(minutes=time)
                        elif "giờ trước" in time:
                            strings = [s for s in time.split() if s.isdigit()]
                            time = strings[0]
                            time = int(time)
                            newtime = datetime.now() - timedelta(hours=time)
                        elif "ngày trước" in time:
                            strings = [s for s in time.split() if s.isdigit()]
                            time = strings[0]
                            time = int(time)
                            newtime = datetime.now() - timedelta(days=time)
                        try:
                            if newTime is not None:
                                newTime = datetime.timestamp(newTime)
                                return newTime
                        except Exception as e:
                            print(e)
