using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Business.Interfaces;
using Dtos.CourtTypeDtos;
using Entities.Concrete;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;

namespace UI.ViewComponents {
    public class CourtTypeSelectList : ViewComponent {

        private readonly IGenericService _genericService;

        public CourtTypeSelectList(IGenericService genericService) {
            _genericService = genericService;
        }

        public async Task<IViewComponentResult> InvokeAsync() {
            var results = await _genericService.GetAll<CourtTypeListDto, CourtType>();
            var data = new SelectList(results.Data, "Id", "Name", "CourtTypeId");
            return View(data);
        }

    }
}