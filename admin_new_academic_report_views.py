class AdminNewAcademicReportView(AdminLoginRequiredMixin, View):

    def get(self, request):

        active_courses = Course.objects.filter(Q(course_active='Y') & Q(is_enterprise=False) &
                                               Q(is_running=True)).order_by('-add_time') .annotate(
         
            batch_count=Count('batch'),
            
            )
        
        course_query = request.GET.get('searchedCourseId', '')
        from_date_filter = request.GET.get('from_date', None)
        to_date_filter = request.GET.get('to_date', None)

        if course_query:
            active_courses = active_courses.filter(name__icontains=course_query).order_by('-is_running')

        search_course = Course.objects.filter(
            Q(course_active='Y') & Q(is_enterprise=False)
        ).order_by('-is_running')

        if from_date_filter and to_date_filter:
            formatted_from_date = datetime.strptime(from_date_filter, '%m/%d/%Y')
            formatted_to_date = datetime.strptime(to_date_filter, '%m/%d/%Y')

            # Use filter to check the date range on the active batch's live class dates
            active_courses = active_courses.filter(
                batch__live_class_from__gte=formatted_from_date,
                batch__live_class_to__lte=formatted_to_date,
                batch__batch_active="Y"
            )
        
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(active_courses, 20)
        all_courses = p.page(page)


        return render(request, 'admin_new_academic_report.html',                      
                      {"ActiveCourses": all_courses,
                       'course_count': active_courses.count(),
                       'Search_Courses': active_courses.distinct(),
                       })
    l