using Business.Interfaces;
using Dtos.StreamDtos;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;

namespace UI.ViewComponents {
    public class StreamSelectListByPlayerFilter : ViewComponent {

        private readonly IGenericService _genericService;

        public StreamSelectListByPlayerFilter(IGenericService genericService) {
            _genericService = genericService;
        }

        public async Task<IViewComponentResult> InvokeAsync(long playerId) {
            var results = await _genericService.GetListByFilter<StreamListDto, Entities.Concrete.Stream>(x => x.PlayerId == playerId);
            var data = new SelectList(results.Data, "Id", "Name", "StreamId");
            return View(data);
        }

    }
}